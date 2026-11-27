"use client";

import { useCallback, useEffect, useId, useRef, useState } from "react";

import { DATE_LOCALES } from "@/i18n";
import { useI18n } from "@/i18n/client";
import { ApiError, requestChallenge, verifyOwnership } from "@/lib/api";
import { forgetChallenge, loadChallenge, saveChallenge } from "@/lib/pendingProof";
import type { OwnershipChallenge, OwnershipProof, ProofMethod, ScanReport } from "@/lib/types";

import { ActiveScan } from "./ActiveScan";
import { CopyButton } from "./CopyButton";
import { Label, Section } from "./Section";

const METHODS: ProofMethod[] = ["meta", "file", "dns"];
const CHECK_EVERY_MS = 30_000;
const MAX_AUTOMATIC_CHECKS = 120; // one hour, then the visitor clicks "Check now"
// Errors that mean "not there yet": keep checking. Anything else stops the automatic checks.
const KEEP_WAITING = new Set(["proof_not_found", "network", "timeout", "unreachable"]);
const TIME_OPTIONS: Intl.DateTimeFormatOptions = {
  day: "numeric",
  month: "short",
  hour: "2-digit",
  minute: "2-digit",
};

type Who = "someone" | "me";

interface OwnershipVerificationProps {
  target: string;
  onActiveReport: (report: ScanReport) => void;
  /** Hosted platform the site runs on (Shopify, Wix...): the active scan does not apply. */
  hostedPlatform?: string | null;
}

/**
 * Proof of domain ownership, required before an active scan, in the way Google Search
 * Console does it:
 * 1. publish a code: either forward a ready-made message to whoever runs the website,
 *    or do it yourself with one of three methods (HTML tag, file, DNS record),
 * 2. Vigilo looks for the code by itself every 30 seconds, with every method,
 * 3. the domain is verified and the active scan can start.
 * The pending code is kept in this browser so the owner can come back later; the
 * ownership pass only lives in this component's state.
 */
export function OwnershipVerification({ target, onActiveReport, hostedPlatform }: OwnershipVerificationProps) {
  const { t, locale } = useI18n();
  const a = t.active;
  const id = useId();
  // A code requested earlier for this site, maybe forwarded to someone: pick it up again.
  const [challenge, setChallenge] = useState<OwnershipChallenge | null>(() => loadChallenge(target));
  const [who, setWho] = useState<Who | null>(() => (challenge ? "someone" : null));
  const [method, setMethod] = useState<ProofMethod>("meta");
  const [proof, setProof] = useState<OwnershipProof | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [lastChecked, setLastChecked] = useState<Date | null>(null);
  const [paused, setPaused] = useState(false);
  const checks = useRef(0);
  const publishHeading = useRef<HTMLHeadingElement>(null);
  const verifiedHeading = useRef<HTMLHeadingElement>(null);

  const time = (unix: number) =>
    new Intl.DateTimeFormat(DATE_LOCALES[locale], TIME_OPTIONS).format(new Date(unix * 1000));
  const clock = (date: Date) =>
    new Intl.DateTimeFormat(DATE_LOCALES[locale], { hour: "2-digit", minute: "2-digit" }).format(date);
  const messageOf = useCallback(
    (err: unknown) => {
      if (err instanceof ApiError && err.message) return err.message;
      return err instanceof ApiError && err.code === "network" ? t.errors.network : a.failed;
    },
    [t, a],
  );

  // Move the focus to the step that just appeared, as the rest of the interface does.
  useEffect(() => {
    if (proof) verifiedHeading.current?.focus();
  }, [proof]);

  const check = useCallback(
    async (manual: boolean) => {
      if (!challenge) return;
      if (manual) {
        setBusy(true);
        setError("");
      }
      try {
        const result = await verifyOwnership(challenge.domain, challenge.token, "auto", locale);
        forgetChallenge(target);
        setProof(result);
      } catch (err) {
        const code = err instanceof ApiError ? err.code : "network";
        setLastChecked(new Date());
        if (manual) setError(messageOf(err));
        if (!KEEP_WAITING.has(code)) {
          setError(messageOf(err));
          setPaused(true);
        }
      } finally {
        if (manual) setBusy(false);
      }
    },
    [challenge, locale, target, messageOf],
  );

  // Automatic checks: the person publishing the code may do it later, from elsewhere.
  useEffect(() => {
    if (!challenge || proof || paused) return;
    const timer = window.setInterval(() => {
      checks.current += 1;
      if (checks.current > MAX_AUTOMATIC_CHECKS || Date.now() / 1000 > challenge.expires_at) {
        setPaused(true);
        return;
      }
      void check(false);
    }, CHECK_EVERY_MS);
    return () => window.clearInterval(timer);
  }, [challenge, proof, paused, check]);

  async function start() {
    setBusy(true);
    setError("");
    try {
      const fresh = await requestChallenge(target, locale);
      saveChallenge(target, fresh);
      setChallenge(fresh);
      setProof(null);
      setPaused(false);
      setLastChecked(null);
      checks.current = 0;
      window.setTimeout(() => publishHeading.current?.focus(), 0);
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

  const header = (
    <div>
      <h2 id={`${id}-title`} className="font-serif text-2xl leading-8 font-semibold md:text-[28px] md:leading-9">
        {a.title}
      </h2>
      <p className="mt-2">{a.intro}</p>
    </div>
  );

  if (hostedPlatform) {
    return (
      <Section labelledBy={`${id}-title`} rail={<Label>{a.rail}</Label>} className="print:hidden">
        <div className="flex max-w-[760px] flex-col gap-5">
          {header}
          <p className="border-s-2 border-ink ps-4">{a.hosted(hostedPlatform)}</p>
        </div>
      </Section>
    );
  }

  return (
    <Section labelledBy={`${id}-title`} rail={<Label>{a.rail}</Label>} className="print:hidden">
      <div className="flex max-w-[760px] flex-col gap-5">
        {header}

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
              <h3 ref={publishHeading} tabIndex={-1} className="font-semibold">
                {a.steps.publish}
              </h3>
              {proof ? (
                <p className="mt-1 text-sm text-muted">{a.methods[proof.method]}</p>
              ) : (
                <>
                  <ChoiceGroup
                    name={`${id}-who`}
                    legend={a.who.question}
                    value={who}
                    onChange={setWho}
                    options={[
                      { value: "someone", label: a.who.someone, hint: a.who.someoneHint },
                      { value: "me", label: a.who.me, hint: a.who.meHint },
                    ]}
                  />
                  {who === "someone" && <Delegate challenge={challenge} until={time(challenge.expires_at)} />}
                  {who === "me" && (
                    <SelfService challenge={challenge} method={method} onMethodChange={setMethod} name={`${id}-method`} />
                  )}
                  <p className="mt-4 text-sm text-muted">{a.expires(time(challenge.expires_at))}</p>
                </>
              )}
            </Step>

            <Step number={2} done={proof !== null}>
              <h3 className="font-semibold">{a.steps.check}</h3>
              {!proof && (
                <div className="mt-2 flex flex-col gap-3">
                  <p role="status" className="text-sm">
                    {paused ? a.paused : lastChecked ? a.lastChecked(clock(lastChecked)) : a.waiting}
                  </p>
                  <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap">
                    <button
                      type="button"
                      onClick={() => {
                        setPaused(false);
                        checks.current = 0;
                        void check(true);
                      }}
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

            <Step number={3} done={proof !== null} showDone={false}>
              <h3 ref={verifiedHeading} tabIndex={-1} className={proof ? "font-semibold" : "font-semibold text-muted"}>
                {proof ? a.verified(proof.domain) : a.steps.verified}
              </h3>
              {proof && (
                <div className="mt-1 flex flex-col gap-2">
                  <p>{a.validUntil(time(proof.expires_at))}</p>
                  <p className="text-sm text-muted">{a.keepProof}</p>
                  <ActiveScan proof={proof} token={challenge.token} onReport={onActiveReport} />
                </div>
              )}
            </Step>
          </ol>
        )}
      </div>
    </Section>
  );
}

/** The ready-made message for whoever runs the website: email, WhatsApp or copy. */
function Delegate({ challenge, until }: { challenge: OwnershipChallenge; until: string }) {
  const { t } = useI18n();
  const d = t.active.delegate;
  const message = d.message({
    domain: challenge.domain,
    tag: challenge.meta.tag,
    fileName: challenge.file.name,
    fileUrl: challenge.file.url,
    code: challenge.token,
    dnsName: challenge.dns.name,
    dnsValue: challenge.dns.value,
    until,
  });
  const subject = d.subject(challenge.domain);
  const mail = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(message)}`;
  const whatsapp = `https://wa.me/?text=${encodeURIComponent(message)}`;

  return (
    <div className="mt-4 flex flex-col gap-3">
      <p>{d.intro}</p>
      <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap">
        <a
          href={mail}
          className="inline-flex h-12 items-center rounded-xs bg-stamp px-6 font-semibold text-white no-underline"
        >
          {d.email}
        </a>
        <a
          href={whatsapp}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex h-12 items-center rounded-xs border border-ink px-5 font-semibold no-underline"
        >
          {d.whatsapp}
        </a>
      </div>
      <div className="flex flex-col border border-rule md:flex-row md:items-start">
        <p dir="auto" className="min-w-0 grow px-3.5 py-3 text-sm leading-6 whitespace-pre-wrap wrap-anywhere">
          {message}
        </p>
        <CopyButton text={message} label={d.copy} />
      </div>
    </div>
  );
}

/** The three methods, with the values to copy and step-by-step guides. */
function SelfService({
  challenge,
  method,
  onMethodChange,
  name,
}: {
  challenge: OwnershipChallenge;
  method: ProofMethod;
  onMethodChange: (method: ProofMethod) => void;
  name: string;
}) {
  const { t } = useI18n();
  const a = t.active;

  function download() {
    const url = URL.createObjectURL(new Blob([challenge.file.content], { type: "text/plain" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = challenge.file.name;
    document.body.append(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 10_000);
  }

  return (
    <div className="mt-4 flex flex-col gap-4">
      <ChoiceGroup
        name={name}
        legend={a.methodsTitle}
        value={method}
        onChange={onMethodChange}
        options={METHODS.map((m) => ({ value: m, label: a.methods[m], hint: a.methodHints[m] }))}
      />

      <div>
        {method === "meta" && (
          <>
            <p className="text-sm">{a.metaInstructions}</p>
            <dl className="mt-2 flex flex-col gap-2">
              <CopyField label={a.metaLabel} value={challenge.meta.tag} />
            </dl>
          </>
        )}
        {method === "file" && (
          <>
            <p className="text-sm">{a.fileInstructions}</p>
            <dl className="mt-2 flex flex-col gap-2">
              <CopyField label={a.fileAddress} value={challenge.file.url} />
            </dl>
            <button
              type="button"
              onClick={download}
              className="mt-3 h-12 cursor-pointer rounded-xs border border-ink px-5 font-semibold"
            >
              {a.download(challenge.file.name)}
            </button>
          </>
        )}
        {method === "dns" && (
          <>
            <p className="text-sm">{a.dnsInstructions}</p>
            <dl className="mt-2 flex flex-col gap-2">
              <CopyField label={a.recordType} value={challenge.dns.type} />
              <CopyField label={a.recordName} value={challenge.dns.name} />
              <CopyField label={a.recordValue} value={challenge.dns.value} />
            </dl>
            <p className="mt-2 text-sm text-muted">{a.dnsDelay}</p>
          </>
        )}
      </div>

      <Guides method={method} name={`${name}-guide`} />
    </div>
  );
}

function Guides({ method, name }: { method: ProofMethod; name: string }) {
  const { t } = useI18n();
  const a = t.active;
  const guides = a.guides[method];
  const [chosen, setChosen] = useState(0);
  const guide = guides[Math.min(chosen, guides.length - 1)];

  return (
    <details className="border-t border-rule pt-3">
      <summary className="min-h-11 cursor-pointer font-semibold">{a.guidesTitle}</summary>
      <fieldset className="mt-3">
        <legend className="text-sm text-muted">{a.guidesFor}</legend>
        <div className="mt-2 flex flex-wrap gap-x-5 gap-y-2">
          {guides.map((g, index) => (
            <label key={g.name} className="flex cursor-pointer items-center gap-2 text-sm">
              <input
                type="radio"
                name={name}
                checked={index === chosen}
                onChange={() => setChosen(index)}
                className="size-4 cursor-pointer accent-ink"
              />
              {g.name}
            </label>
          ))}
        </div>
      </fieldset>
      <ol className="mt-3 list-decimal ps-6 text-sm leading-6">
        {guide.steps.map((step) => (
          <li key={step} className="py-1">
            {step}
          </li>
        ))}
      </ol>
      <p className="mt-2 text-sm text-muted">{a.guidesNote}</p>
    </details>
  );
}

function ChoiceGroup<T extends string>({
  name,
  legend,
  value,
  onChange,
  options,
}: {
  name: string;
  legend: string;
  value: T | null;
  onChange: (value: T) => void;
  options: { value: T; label: string; hint: string }[];
}) {
  return (
    <fieldset className="mt-3">
      <legend className="text-sm text-muted">{legend}</legend>
      <div className="mt-2 flex flex-col gap-3">
        {options.map((option) => (
          <label key={option.value} className="flex cursor-pointer items-start gap-3">
            <input
              type="radio"
              name={name}
              value={option.value}
              checked={value === option.value}
              onChange={() => onChange(option.value)}
              className="mt-1 size-4 shrink-0 cursor-pointer accent-ink"
            />
            <span>
              <span className="font-semibold">{option.label}</span>
              <span className="block text-sm text-muted">{option.hint}</span>
            </span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}

function Step({
  number,
  done,
  showDone = true,
  children,
}: {
  number: number;
  done: boolean;
  /** The last step says it in its heading. */
  showDone?: boolean;
  children: React.ReactNode;
}) {
  const { t } = useI18n();
  return (
    <li className="grid grid-cols-[32px_minmax(0,1fr)] gap-x-3 border-b border-rule py-4">
      <span className="font-mono text-sm leading-6">{number}</span>
      <div className="min-w-0">
        {children}
        {done && showDone && <p className="mt-1 font-mono text-[13px] text-pass">{t.active.stepDone}</p>}
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
