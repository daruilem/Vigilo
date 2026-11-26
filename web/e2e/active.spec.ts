import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

import { MESSAGES } from "../src/i18n";

import { makeReport, simulateActiveScan, simulateApi } from "./api";

const t = MESSAGES.en;
const a = t.active;

// The active scan screens only exist in builds made with NEXT_PUBLIC_VIGILO_ACTIVE_SCAN=1.
test.skip(process.env.NEXT_PUBLIC_VIGILO_ACTIVE_SCAN !== "1", "active scan not enabled in this build");

test("from the check-up to a verified active scan and back", async ({ page }) => {
  await simulateApi(page, [makeReport("first")]);
  await simulateActiveScan(page);
  await page.goto("/en");
  await page.getByLabel(t.form.urlLabel).fill("shop.example");
  await page.getByLabel(t.form.authorize).check();
  await page.getByRole("button", { name: t.form.submit }).click();
  await expect(page.getByRole("heading", { level: 1, name: t.report.title })).toBeVisible();

  // Proof of ownership.
  await page.getByRole("button", { name: a.start }).click();
  await page.getByRole("radio", { name: new RegExp(a.who.someone) }).check();
  await expect(page.getByRole("link", { name: a.delegate.email })).toBeVisible();
  await page.getByRole("radio", { name: new RegExp(a.who.me) }).check();
  await expect(page.getByText('<meta name="vigilo-verification" content="abc.1800000000.def">')).toBeVisible();
  const proof = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
  expect(proof.violations.map((v) => v.id)).toEqual([]);
  if (process.env.E2E_SCREENSHOTS) {
    await page.getByText(a.guidesTitle, { exact: true }).click();
    await page.locator("section").filter({ hasText: a.title }).screenshot({
      path: `test-results/proof-${test.info().project.name}.png`,
    });
  }
  await page.getByRole("button", { name: a.verify }).click();
  await expect(page.getByRole("heading", { name: a.verified("shop.example") })).toBeVisible();

  // Conditions: refused until accepted.
  await page.getByRole("button", { name: a.launch }).click();
  await expect(page.getByText(a.mustAccept)).toBeVisible();
  const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
  expect(results.violations.map((v) => v.id)).toEqual([]);
  await page.getByRole("checkbox", { name: a.accept }).check();
  await page.getByRole("button", { name: a.launch }).click();

  // The active report replaces the screen, with its own title and grade.
  await expect(page.getByRole("heading", { level: 1, name: a.reportTitle })).toBeFocused();
  await expect(page.getByRole("img", { name: t.report.gradeLabel("B") })).toBeVisible();
  await expect(page.getByText(a.separateGrade)).toBeVisible();
  await expect(page.getByRole("heading", { name: "Private files or information can be read" })).toBeVisible();
  const report = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
  expect(report.violations.map((v) => v.id)).toEqual([]);
  if (process.env.E2E_SCREENSHOTS) {
    await page.screenshot({ path: `test-results/active-report-${test.info().project.name}.png`, fullPage: true });
  }

  // Back to the check-up it was started from.
  await page.getByRole("button", { name: a.back }).click();
  await expect(page.getByRole("heading", { level: 1, name: t.report.title })).toBeFocused();
  await expect(page.getByRole("img", { name: t.report.gradeLabel("C") })).toBeVisible();
});
