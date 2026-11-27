import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { MESSAGES } from "@/i18n";
import { loadChallenge, saveChallenge } from "@/lib/pendingProof";
import type { OwnershipChallenge, OwnershipProof } from "@/lib/types";

import { OwnershipVerification } from "./OwnershipVerification";

const a = MESSAGES.en.active;
const TOKEN = "abc.1800000000.def";

const challenge: OwnershipChallenge = {
  domain: "shop.example",
  token: TOKEN,
  expires_at: 1_800_000_000,
  meta: { tag: `<meta name="vigilo-verification" content="${TOKEN}">` },
  file: { name: "vigilo-abc.txt", url: "https://shop.example/vigilo-abc.txt", content: TOKEN },
  dns: { name: "_vigilo.shop.example", type: "TXT", value: `vigilo-verification=${TOKEN}` },
};
const proof: OwnershipProof = {
  domain: "shop.example",
  method: "meta",
  ownership_pass: "meta.1800000000.signed",
  expires_at: 1_800_000_000,
};
const notYet = { detail: { code: "proof_not_found", message: "The code is not published on shop.example yet." } };

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

function setup(responses: Response[], hostedPlatform: string | null = null, fakeTimers = false) {
  const fetchMock = vi.fn(async () => responses.shift() ?? json(notYet, 422));
  vi.stubGlobal("fetch", fetchMock);
  render(
    <OwnershipVerification target="shop.example" onActiveReport={() => {}} hostedPlatform={hostedPlatform} />,
  );
  const user = fakeTimers ? userEvent.setup({ advanceTimers: vi.advanceTimersByTime }) : userEvent.setup();
  return { user, fetchMock };
}

function bodyOf(fetchMock: ReturnType<typeof vi.fn>, call: number) {
  const [url, init] = fetchMock.mock.calls[call] as unknown as [string, RequestInit];
  return { url, body: JSON.parse(init.body as string) as Record<string, string> };
}

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
  window.localStorage.clear();
});

describe("OwnershipVerification", () => {
  it("explains that sites on hosted platforms cannot be scanned", () => {
    setup([], "Shopify");
    expect(screen.getByText(a.hosted("Shopify"))).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: a.start })).not.toBeInTheDocument();
  });

  it("writes the message for whoever runs the website", async () => {
    const { user, fetchMock } = setup([json(challenge)]);
    await user.click(screen.getByRole("button", { name: a.start }));
    // The code arrives asynchronously: wait for it before going on.
    await screen.findByRole("heading", { name: a.steps.publish });
    expect(bodyOf(fetchMock, 0)).toEqual({
      url: "http://localhost:8000/api/v1/ownership/challenge",
      body: { target: "shop.example", lang: "en" },
    });
    expect(screen.getByRole("heading", { name: a.steps.publish })).toHaveFocus();
    expect(loadChallenge("shop.example", 0)).toEqual(challenge);

    await user.click(screen.getByRole("radio", { name: new RegExp(a.who.someone) }));
    const message = screen.getByText((text) => text.startsWith("Hello,"));
    for (const part of [challenge.meta.tag, challenge.file.url, challenge.dns.name, challenge.dns.value]) {
      expect(message).toHaveTextContent(part);
    }
    const email = screen.getByRole("link", { name: a.delegate.email });
    expect(email.getAttribute("href")).toMatch(/^mailto:\?subject=Please%20verify%20shop\.example/);
    expect(decodeURIComponent(email.getAttribute("href") ?? "")).toContain(challenge.meta.tag);
    const whatsapp = screen.getByRole("link", { name: a.delegate.whatsapp });
    expect(whatsapp.getAttribute("href")).toMatch(/^https:\/\/wa\.me\/\?text=/);
    expect(screen.getByRole("button", { name: a.delegate.copy })).toBeInTheDocument();
  });

  it("shows each method with the values to copy and its guides", async () => {
    const { user } = setup([json(challenge)]);
    await user.click(screen.getByRole("button", { name: a.start }));
    // The code arrives asynchronously: wait for it before going on.
    await screen.findByRole("heading", { name: a.steps.publish });
    await user.click(screen.getByRole("radio", { name: new RegExp(a.who.me) }));

    expect(screen.getByRole("radio", { name: new RegExp(a.methods.meta) })).toBeChecked();
    expect(screen.getByText(challenge.meta.tag)).toBeInTheDocument();
    expect(screen.getByText(a.guides.meta[0].steps[0])).toBeInTheDocument();

    await user.click(screen.getByRole("radio", { name: new RegExp(a.methods.file) }));
    expect(screen.getByText(challenge.file.url)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: a.download("vigilo-abc.txt") })).toBeInTheDocument();

    await user.click(screen.getByRole("radio", { name: new RegExp(a.methods.dns) }));
    expect(screen.getByText(challenge.dns.value)).toBeInTheDocument();
    await user.click(screen.getByRole("radio", { name: "Cloudflare" }));
    expect(screen.getByText(a.guides.dns[0].steps[1])).toBeInTheDocument();
  });

  it("checks every method at once, says what is missing, then confirms", async () => {
    const { user, fetchMock } = setup([json(challenge), json(notYet, 422), json(proof)]);
    await user.click(screen.getByRole("button", { name: a.start }));
    // The code arrives asynchronously: wait for it before going on.
    await screen.findByRole("heading", { name: a.steps.publish });

    await user.click(screen.getByRole("button", { name: a.verify }));
    expect(bodyOf(fetchMock, 1).body).toEqual({ target: "shop.example", token: TOKEN, method: "auto", lang: "en" });
    expect(screen.getByRole("alert")).toHaveTextContent("The code is not published on shop.example yet.");

    await user.click(screen.getByRole("button", { name: a.verify }));
    expect(screen.getByRole("heading", { name: a.verified("shop.example") })).toHaveFocus();
    expect(screen.getByText(a.conditionsTitle)).toBeInTheDocument();
    expect(loadChallenge("shop.example", 0)).toBeNull();
  });

  it("checks by itself every 30 seconds", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const { user, fetchMock } = setup([json(challenge), json(notYet, 422), json(proof)], null, true);
    await user.click(screen.getByRole("button", { name: a.start }));
    // The code arrives asynchronously: wait for it before going on.
    await screen.findByRole("heading", { name: a.steps.publish });
    expect(fetchMock).toHaveBeenCalledTimes(1);

    await act(async () => vi.advanceTimersByTime(30_000));
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(screen.getByText(/not published yet/)).toBeInTheDocument();

    await act(async () => vi.advanceTimersByTime(30_000));
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(screen.getByRole("heading", { name: a.verified("shop.example") })).toBeInTheDocument();
  });

  it("picks up a code requested earlier, for example forwarded yesterday", () => {
    saveChallenge("shop.example", challenge);
    setup([]);
    expect(screen.queryByRole("button", { name: a.start })).not.toBeInTheDocument();
    expect(screen.getByRole("radio", { name: new RegExp(a.who.someone) })).toBeChecked();
    expect(screen.getByText(a.waiting)).toBeInTheDocument();
  });

  it("forgets an expired code", () => {
    saveChallenge("shop.example", { ...challenge, expires_at: 1 });
    setup([]);
    expect(screen.getByRole("button", { name: a.start })).toBeInTheDocument();
  });
});
