import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";

import { MESSAGES } from "@/i18n";
import { loadSnapshot, snapshotOf } from "@/lib/history";
import { finding, report } from "@/test/fixtures";

import { Progress } from "./Progress";

const t = MESSAGES.en;
const hsts = finding({ id: "headers.hsts" });
const git = finding({ id: "files.git", severity: "high", headline: "Your Git folder can be downloaded" });

afterEach(() => window.localStorage.clear());

describe("Progress", () => {
  it("stores nothing until the visitor asks, then can forget", async () => {
    const user = userEvent.setup();
    const current = report([hsts]);
    render(<Progress report={current} previous={null} />);

    expect(window.localStorage.length).toBe(0);
    await user.click(screen.getByRole("button", { name: t.progress.remember }));
    expect(loadSnapshot("shop.example")).not.toBeNull();
    expect(screen.getByRole("status")).toHaveTextContent(t.progress.remembered);

    await user.click(screen.getByRole("button", { name: t.progress.forget }));
    expect(window.localStorage.length).toBe(0);
    expect(screen.getByRole("status")).toHaveTextContent(t.progress.forgotten);
  });

  it("shows what was fixed, what is new and the score change", () => {
    const previous = { ...snapshotOf(report([hsts, git])), score: 34, grade: "F" };
    const current = { ...report([hsts]), score: 80, grade: "B" };
    render(<Progress report={current} previous={previous} />);

    expect(screen.getByRole("heading", { name: t.progress.title })).toBeInTheDocument();
    expect(screen.getByText("(+46)")).toBeInTheDocument();
    expect(screen.getByText("F → B")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: t.progress.fixed(1) })).toBeInTheDocument();
    expect(screen.getByText("Your Git folder can be downloaded")).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: t.progress.added(1) })).not.toBeInTheDocument();
    expect(screen.getByText(t.progress.remaining(1))).toBeInTheDocument();
  });

  it("says so when nothing changed", () => {
    const current = report([hsts]);
    render(<Progress report={current} previous={snapshotOf(current)} />);
    expect(screen.getByText(t.progress.noChange)).toBeInTheDocument();
  });
});
