"use client";

import { useId, useRef, useState, type FormEvent } from "react";

import { useI18n } from "@/i18n/client";

interface ScanFormProps {
  initialTarget?: string;
  onSubmit: (target: string) => void;
}

export function ScanForm({ initialTarget = "", onSubmit }: ScanFormProps) {
  const { t } = useI18n();
  const [target, setTarget] = useState(initialTarget);
  const [authorized, setAuthorized] = useState(false);
  const [errors, setErrors] = useState<{ url?: string; authorized?: string }>({});
  const urlRef = useRef<HTMLInputElement>(null);
  const checkboxRef = useRef<HTMLInputElement>(null);
  const id = useId();

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const next = {
      url: target.trim() ? undefined : t.validation.emptyUrl,
      authorized: authorized ? undefined : t.validation.notAuthorized,
    };
    setErrors(next);
    if (next.url) return urlRef.current?.focus();
    if (next.authorized) return checkboxRef.current?.focus();
    onSubmit(target.trim());
  }

  return (
    <form noValidate onSubmit={submit} className="flex max-w-[560px] flex-col gap-4">
      <div className="flex flex-col gap-2">
        <label htmlFor={`${id}-url`} className="label-caps">
          {t.form.urlLabel}
        </label>
        <input
          ref={urlRef}
          id={`${id}-url`}
          name="url"
          type="text"
          dir="ltr"
          inputMode="url"
          autoComplete="url"
          autoCapitalize="none"
          spellCheck={false}
          value={target}
          onChange={(e) => setTarget(e.target.value)}
          aria-invalid={errors.url ? true : undefined}
          aria-describedby={`${id}-url-hint${errors.url ? ` ${id}-url-error` : ""}`}
          className="h-12 rounded-xs border border-ink bg-transparent px-3.5 font-mono text-base"
        />
        <p id={`${id}-url-hint`} className="text-sm text-muted">
          {t.form.urlHint}
        </p>
        {errors.url && <ErrorText id={`${id}-url-error`}>{errors.url}</ErrorText>}
      </div>

      <div className="flex flex-col gap-2">
        <label className="flex cursor-pointer items-start gap-3">
          <input
            ref={checkboxRef}
            type="checkbox"
            checked={authorized}
            onChange={(e) => setAuthorized(e.target.checked)}
            aria-invalid={errors.authorized ? true : undefined}
            aria-describedby={errors.authorized ? `${id}-auth-error` : undefined}
            className="mt-0.5 size-5 shrink-0 cursor-pointer accent-ink"
          />
          <span>{t.form.authorize}</span>
        </label>
        {errors.authorized && <ErrorText id={`${id}-auth-error`}>{errors.authorized}</ErrorText>}
      </div>

      <div>
        <button
          type="submit"
          className="h-12 w-full cursor-pointer rounded-xs bg-stamp px-6 font-semibold text-white sm:w-auto"
        >
          {t.form.submit}
        </button>
      </div>
    </form>
  );
}

function ErrorText({ id, children }: { id: string; children: React.ReactNode }) {
  return (
    <p id={id} className="flex gap-2.5 text-sm text-high">
      <span aria-hidden="true" className="font-mono font-medium">
        !
      </span>
      <span>{children}</span>
    </p>
  );
}
