"use client";

import { useEffect, useId, useRef, useState } from "react";

import { DATE_LOCALES } from "@/i18n";
import { useI18n } from "@/i18n/client";
import { ApiError, requestChallenge, verifyOwnership } from "@/lib/api";
import type { OwnershipChallenge, OwnershipProof, ProofMethod } from "@/lib/types";

import { CopyButton } from "./CopyButton";
import { Label, Section } from "./Section";

const METHODS: ProofMethod[] = ["dns", "file"];
const TIME_OPTIONS: Intl.DateTimeFormatOptions = {
  day: "numeric",
  month: "short",
  hour: "2-digit",
  minute: "2-digit",
};

/**
 * Proof of domain ownership, required before an active scan:
 * 1. get a code and choose where to publish it (DNS record or file),
 * 2. ask the server to look for it,
 * 3. the domain is verified.
 * The ownership pass only lives in this component's state: nothing is stored.
 */
export function OwnershipVerification({ target }: { target: string }) {
  const { t, locale } = useI18n();
  const id = useId();
  const [challenge, setChallenge] = useState<OwnershipChallenge | null>(null);
  const [method, setMethod] = useState<ProofMethod>("dns");
  const [proof, setProof] = useState<OwnershipProof | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const proofHeading = useRef<HTMLHeadingElement>(null);
  const verifiedHeading = useRef<HTMLHeadingElement>(null);

  // Move the focus to the step that just appeared, as the rest of the interface does.
  useEffect(() => {
    if (proof) verifiedHeading.current?.focus();
    else if (challenge) proofHeading.current?.focus();
  }, [challenge, proof]);

  const a = t.active;
  const time = (unix: number) =>
    new Intl.DateTimeFormat(DATE_LOCALES[locale], TIME_OPTIONS).format(new Date(unix * 1000));
  const messageOf = (err: unknown) => {
    if (err instanceof ApiError && err.message) return err.message;
    return err instanceof ApiError && err.code === "network" ? t.errors.network : a.failed;
  };

  async function start() {
    setBusy(true);
    setError("");
    try {
      setChallenge(await requestChallenge(target, locale));
      setProof(null);
    } catch (err) {
      setError(messageOf(err));
    } finally {
      setBusy(false);
    }
  }

  async function verify() {
    if (!challenge) return;
    setBusy(true);
    setError("");
    try {
      setProof(await verifyOwnership(challenge.domain, challenge.token, method, locale));
    } catch (err) {
      setError(messageOf(err));
    } finally {
      setBusy(false);
    }
  }

  const errorText = error && (
    <p role="alert" className="flex gap-2.5 text-sm text-high">
      <span aria-hidden="true" className="font-mono font-medium">
        !
      </span>
      <span>{error}</span>
    </p>
  );

  return (
    <Section labelledBy={`${id}-title`} rail={<Label>{a.rail}</Label>} className="print:hidden">
      <div className="flex max-w-[760px] flex-col gap-5">
        <div>
          <h2 id={`${id}-title`} className="font-serif text-2xl leading-8 font-semibold md:text-[28px] md:leading-9">
            {a.title}
          </h2>
          <p className="mt-2">{a.intro}</p>
        </div>

        {!challenge && (
          <div className="flex flex-col gap-3">
            <div>
              <button
                type="button"
                onClick={start}
                disabled={busy}
                aria-busy={busy}
                className="h-12 cursor-pointer rounded-xs border border-ink px-5 font-semibold disabled:cursor-wait"
              >
                {busy ? a.preparing : a.start}
              </button>
            </div>
            {errorText}
          </div>
        )}

        {challenge && (
          <ol className="border-t border-ink">
            <Step number={1} done={proof !== null}>
              <h3
                ref={proofHeading}
                tabIndex={-1}
                className="font-semibold"
              >
                {a.steps.choose}
              </h3>
              {proof ? (
                <p className="mt-1 text-sm text-muted">{a.methods[proof.method]}</p>
              ) : (
                <>
                  <fieldset className="mt-3">
                    <legend className="sr-only">{a.steps.choose}</legend>
                    <div className="flex flex-col gap-3">
                      {METHODS.map((m) => (
                        <label key={m} className="flex cursor-pointer items-start gap-3">
                          <input
                            type="radio"
                            name={`${id}-method`}
                            value={m}
                            checked={method === m}
                            onChange={() => setMethod(m)}
                            className="mt-1 size-4 shrink-0 cursor-pointer accent-ink"
                          />
                          <span>
                            <span className="font-semibold">{a.methods[m]}</span>
                            <span className="block text-sm text-muted">{a.methodHints[m]}</span>
                          </span>
                        </label>
                      ))}
                    </div>
                  </fieldset>

                  <div className="mt-4">
                    {method === "dns" ? (
                      <>
                        <p className="text-sm">{a.dnsInstructions}</p>
                        <dl className="mt-2 flex flex-col gap-2">
                          <CopyField label={a.recordType} value={challenge.dns.type} />
                          <CopyField label={a.recordName} value={challenge.dns.name} />
                          <CopyField label={a.recordValue} value={challenge.dns.value} />
                        </dl>
                        <p className="mt-2 text-sm text-muted">{a.dnsDelay}</p>
                      </>
                    ) : (
                      <>
                        <p className="text-sm">{a.fileInstructions}</p>
                        <dl className="mt-2 flex flex-col gap-2">
                          <CopyField label={a.fileAddress} value={challenge.file.url} />
                          <CopyField label={a.fileContent} value={challenge.file.content} />
                        </dl>
                      </>
                    )}
                    <p className="mt-2 text-sm text-muted">{a.expires(time(challenge.expires_at))}</p>
                  </div>
                </>
              )}
            </Step>

            <Step number={2} done={proof !== null}>
              <h3 className="font-semibold">{a.steps.verify}</h3>
              {!proof && (
                <div className="mt-3 flex flex-col gap-3">
                  <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap">
                    <button
                      type="button"
                      onClick={verify}
                      disabled={busy}
                      aria-busy={busy}
                      className="h-12 cursor-pointer rounded-xs bg-stamp px-6 font-semibold text-white disabled:cursor-wait disabled:opacity-80"
                    >
                      {busy ? a.verifying : a.verify}
                    </button>
                    <button
                      type="button"
                      onClick={start}
                      disabled={busy}
                      className="h-12 cursor-pointer rounded-xs border border-ink px-5 font-semibold disabled:cursor-wait"
                    >
                      {a.newCode}
                    </button>
                  </div>
                  {errorText}
                </div>
              )}
            </Step>

            <Step number={3} done={proof !== null}>
              <h3 ref={verifiedHeading} tabIndex={-1} className={proof ? "font-semibold" : "font-semibold text-muted"}>
                {proof ? a.verified(proof.domain) : a.steps.verified}
              </h3>
              {proof && (
                <div className="mt-1 flex flex-col gap-2">
                  <p>{a.validUntil(time(proof.expires_at))}</p>
                  <p className="text-sm text-muted">{a.keepProof}</p>
                  <p className="text-sm">{a.comingSoon}</p>
                </div>
              )}
            </Step>
          </ol>
        )}
      </div>
    </Section>
  );
}

function Step({ number, done, children }: { number: number; done: boolean; children: React.ReactNode }) {
  const { t } = useI18n();
  return (
    <li className="grid grid-cols-[32px_minmax(0,1fr)] gap-x-3 border-b border-rule py-4">
      <span className="font-mono text-sm leading-6">{number}</span>
      <div className="min-w-0">
        {children}
        {done && <p className="mt-1 font-mono text-[13px] text-pass">{t.active.stepDone}</p>}
      </div>
    </li>
  );
}

function CopyField({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col border border-rule md:flex-row md:items-start">
      <dt className="shrink-0 px-3.5 pt-2.5 text-sm text-muted md:w-28 md:py-3">{label}</dt>
      <dd className="flex min-w-0 grow flex-col md:flex-row md:items-start">
        <span dir="ltr" className="min-w-0 grow px-3.5 pb-2.5 font-mono text-[13px] leading-5 wrap-anywhere md:py-3">
          {value}
        </span>
        <CopyButton text={value} />
      </dd>
    </div>
  );
}
