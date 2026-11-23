import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { MESSAGES } from "@/i18n";
import type { OwnershipChallenge, OwnershipProof } from "@/lib/types";

import { OwnershipVerification } from "./OwnershipVerification";

const a = MESSAGES.en.active;

const challenge: OwnershipChallenge = {
  domain: "shop.example",
  token: "abc.1800000000.def",
  expires_at: 1_800_000_000,
  dns: { name: "_vigilo.shop.example", type: "TXT", value: "vigilo-verification=abc.1800000000.def" },
  file: { url: "https://shop.example/.well-known/vigilo-verification.txt", content: "abc.1800000000.def" },
};
const proof: OwnershipProof = {
  domain: "shop.example",
  method: "file",
  ownership_pass: "file.1800000000.signed",
  expires_at: 1_800_000_000,
};

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

function setup(...responses: (Response | Error)[]) {
  const fetchMock = vi.fn(async () => {
    const next = responses.shift();
    if (next instanceof Error) throw next;
    return next ?? json({});
  });
  vi.stubGlobal("fetch", fetchMock);
  render(<OwnershipVerification target="shop.example" />);
  return { user: userEvent.setup(), fetchMock };
}

function bodyOf(fetchMock: ReturnType<typeof vi.fn>, call: number) {
  const [url, init] = fetchMock.mock.calls[call] as unknown as [string, RequestInit];
  return { url, body: JSON.parse(init.body as string) as Record<string, string> };
}

afterEach(() => vi.unstubAllGlobals());

describe("OwnershipVerification", () => {
  it("shows the DNS record to publish, ready to copy", async () => {
    const { user, fetchMock } = setup(json(challenge));
    await user.click(screen.getByRole("button", { name: a.start }));

    expect(bodyOf(fetchMock, 0)).toEqual({
      url: "http://localhost:8000/api/v1/ownership/challenge",
      body: { target: "shop.example", lang: "en" },
    });
    expect(screen.getByRole("heading", { name: a.steps.choose })).toHaveFocus();
    expect(screen.getByRole("radio", { name: new RegExp(a.methods.dns) })).toBeChecked();
    expect(screen.getByText("_vigilo.shop.example")).toBeInTheDocument();
    expect(screen.getByText(challenge.dns.value)).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: MESSAGES.en.report.copy })).toHaveLength(3);
  });

  it("verifies with the file method and shows the result", async () => {
    const { user, fetchMock } = setup(json(challenge), json(proof));
    await user.click(screen.getByRole("button", { name: a.start }));
    await user.click(screen.getByRole("radio", { name: new RegExp(a.methods.file) }));
    expect(screen.getByText(challenge.file.url)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: a.verify }));
    expect(bodyOf(fetchMock, 1).body).toEqual({
      target: "shop.example",
      token: challenge.token,
      method: "file",
      lang: "en",
    });
    const verified = screen.getByRole("heading", { name: a.verified("shop.example") });
    expect(verified).toHaveFocus();
    expect(screen.getByText(a.keepProof)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: a.verify })).not.toBeInTheDocument();
  });

  it("shows the server's explanation when the proof is not found, and lets the user retry", async () => {
    const message = "We did not find the TXT record _vigilo.shop.example.";
    const { user } = setup(json(challenge), json({ detail: { code: "record_not_found", message } }, 422));
    await user.click(screen.getByRole("button", { name: a.start }));
    await user.click(screen.getByRole("button", { name: a.verify }));

    expect(screen.getByRole("alert")).toHaveTextContent(message);
    expect(screen.getByRole("button", { name: a.verify })).toBeEnabled();
  });

  it("explains when the service cannot be reached", async () => {
    const { user } = setup(new TypeError("Failed to fetch"));
    await user.click(screen.getByRole("button", { name: a.start }));
    expect(screen.getByRole("alert")).toHaveTextContent(MESSAGES.en.errors.network);
  });
});
