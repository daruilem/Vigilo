import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { MESSAGES } from "@/i18n";
import { I18nProvider } from "@/i18n/client";
import { finding, report } from "@/test/fixtures";

import { Report } from "./Report";

const t = MESSAGES.en;

const issues = [
  finding({ id: "headers.hsts", severity: "medium" }),
  finding({
    id: "files.git",
    check: "files",
    severity: "high",
    headline: "Your Git folder can be downloaded by anyone",
    observed: [{ label: "GET /.git/HEAD", value: "200 OK · 23 bytes" }],
  }),
  finding({
    id: "legal.impressum",
    check: "privacy",
    severity: "medium",
    headline: "No Impressum link on the home page",
    fixes: {},
    recommendation: "Create an Impressum page.",
  }),
];
const passed = finding({
  id: "tls.certificate",
  status: "pass",
  severity: "info",
  headline: "Certificate is valid",
  observed: [{ label: "Issuer", value: "R11" }],
  fixes: {},
});

function renderReport() {
  render(<Report report={report([...issues, passed])} onNewCheck={() => {}} />);
  return userEvent.setup();
}

describe("Report", () => {
  it("shows the grade and the number of issues", () => {
    renderReport();
    expect(screen.getByRole("img", { name: t.report.gradeLabel("D") })).toBeInTheDocument();
    expect(screen.getByText(t.report.issuesCount(3))).toBeInTheDocument();
  });

  it("lists the most serious issue first", () => {
    renderReport();
    const headings = screen.getAllByRole("heading", { level: 2 });
    expect(headings[0]).toHaveTextContent("Your Git folder can be downloaded by anyone");
  });

  it("marks legal points as not graded and shows their recommendation", () => {
    renderReport();
    const section = screen.getByRole("region", { name: "No Impressum link on the home page" });
    expect(within(section).getByText(t.report.notGraded)).toBeInTheDocument();
    expect(within(section).getByText("Create an Impressum page.")).toBeInTheDocument();
  });

  it("applies one hosting choice to every section", async () => {
    const user = renderReport();
    const nginxTabs = screen.getAllByRole("tab", { name: "Nginx" });
    await user.click(nginxTabs[0]);
    for (const tab of screen.getAllByRole("tab", { name: "Nginx" })) {
      expect(tab).toHaveAttribute("aria-selected", "true");
    }
  });

  it("supports arrow keys in the hosting tabs", async () => {
    const user = renderReport();
    const apache = screen.getAllByRole("tab", { name: "Apache" })[0];
    apache.focus();
    await user.keyboard("{ArrowRight}");
    expect(screen.getAllByRole("tab", { name: "Nginx" })[0]).toHaveFocus();
    expect(screen.getAllByRole("tab", { name: "Nginx" })[0]).toHaveAttribute("aria-selected", "true");
  });

  it("folds passed checks until asked", async () => {
    const user = renderReport();
    const toggle = screen.getByRole("button", { name: /1 check passed/ });
    // jsdom does not load the stylesheet, so check the class that hides the list on screen
    // (it stays in the page so that printing shows it).
    const list = document.getElementById(toggle.getAttribute("aria-controls")!)!;
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    expect(list).toHaveClass("hidden");
    await user.click(toggle);
    expect(toggle).toHaveAttribute("aria-expanded", "true");
    expect(list).not.toHaveClass("hidden");
    expect(within(list).getByText("Certificate is valid")).toBeInTheDocument();
  });
});

describe("Report in Arabic", () => {
  it("uses Arabic text and plural rules", () => {
    render(
      <I18nProvider locale="ar">
        <Report report={report([...issues, passed])} onNewCheck={() => {}} />
      </I18nProvider>,
    );
    expect(screen.getByText(MESSAGES.ar.report.issuesCount(3))).toBeInTheDocument();
    expect(MESSAGES.ar.report.issuesCount(3)).toBe("3 مشكلات تحتاج إلى إصلاح");
    expect(MESSAGES.ar.report.issuesCount(2)).toBe("مشكلتان تحتاجان إلى إصلاح");
    expect(screen.getByRole("button", { name: MESSAGES.ar.report.downloadPdf })).toBeInTheDocument();
  });
});

describe("Grade explanation", () => {
  it("opens the A to F scale with the site's grade and score", async () => {
    const user = userEvent.setup();
    render(<Report report={report([passed])} onNewCheck={() => {}} />);
    const toggle = screen.getByRole("button", { name: t.grades.toggle("D") });
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    await user.click(toggle);
    expect(toggle).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("heading", { name: t.grades.title })).toBeInTheDocument();
    const current = screen.getAllByRole("listitem").find((li) => li.getAttribute("aria-current") === "true");
    expect(current).toHaveTextContent(t.grades.meanings.D);
    expect(screen.getByText(t.grades.yourScore(54))).toBeInTheDocument();
  });

  it("hides the active scan preview unless it is turned on", () => {
    renderReport();
    expect(screen.queryByRole("heading", { name: t.active.title })).not.toBeInTheDocument();
  });
});

describe("Report of an active scan", () => {
  it("has its own title, says its grade is separate and goes back to the check-up", async () => {
    const onBack = vi.fn();
    const active = { ...report(issues), kind: "active" as const };
    render(<Report report={active} onNewCheck={() => {}} onBack={onBack} />);
    expect(screen.getByRole("heading", { level: 1, name: t.active.reportTitle })).toBeInTheDocument();
    expect(screen.getByText(t.active.separateGrade)).toBeInTheDocument();
    expect(screen.getByText(t.active.reportMethod)).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: t.progress.offerTitle })).not.toBeInTheDocument();
    await userEvent.setup().click(screen.getByRole("button", { name: t.active.back }));
    expect(onBack).toHaveBeenCalled();
  });
});
