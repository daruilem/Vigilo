import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

import { MESSAGES } from "../src/i18n";

import { makeReport, simulateApi } from "./api";

const t = MESSAGES.en;

/** WCAG 2.1 A and AA, as promised in the README. */
async function expectAccessible(page: Page) {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(results.violations.map((v) => `${v.id}: ${v.help} (${v.nodes.length})`)).toEqual([]);
}

async function checkWebsite(page: Page) {
  await page.getByLabel(t.form.urlLabel).fill("shop.example");
  await page.getByLabel(t.form.authorize).check();
  await page.getByRole("button", { name: t.form.submit }).click();
  await expect(page.getByRole("heading", { level: 1, name: t.report.title })).toBeVisible();
}

test("home page is accessible in every language", async ({ page }) => {
  for (const lang of ["en", "fr", "de", "ar"]) {
    await page.goto(`/${lang}`);
    await expect(page.locator("html")).toHaveAttribute("lang", lang);
    await expect(page.locator("html")).toHaveAttribute("dir", lang === "ar" ? "rtl" : "ltr");
    await expectAccessible(page);
  }
});

test("method page is accessible", async ({ page }) => {
  await page.goto("/en/method");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await expectAccessible(page);
});

test("the form refuses a check without authorisation", async ({ page }) => {
  await page.goto("/en");
  await page.getByLabel(t.form.urlLabel).fill("shop.example");
  await page.getByRole("button", { name: t.form.submit }).click();
  await expect(page.getByText(t.validation.notAuthorized)).toBeVisible();
});

test("a check-up from the form to the PDF", async ({ page }) => {
  await simulateApi(page, [makeReport("first")]);
  await page.goto("/en");
  await checkWebsite(page);

  // Grade, most serious problem first, focus moved to the report title.
  await expect(page.getByRole("img", { name: t.report.gradeLabel("C") })).toBeVisible();
  await expect(page.getByRole("heading", { level: 2 }).first()).toHaveText(
    "Your Git folder can be downloaded by anyone",
  );
  await expect(page.getByRole("heading", { level: 1 })).toBeFocused();
  await expectAccessible(page);

  // The hosting choice changes the code shown.
  const section = page.getByRole("region", { name: "Browsers are not told to always use HTTPS" });
  await section.getByRole("tab", { name: "Nginx" }).click();
  await expect(section.getByText("add_header Strict-Transport-Security")).toBeVisible();

  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: t.report.downloadPdf }).click();
  expect((await download).suggestedFilename()).toBe("vigilo-shop.example-2026-11-26.pdf");
});

test("tabs follow the keyboard pattern", async ({ page }) => {
  await simulateApi(page, [makeReport("first")]);
  await page.goto("/en");
  await checkWebsite(page);

  const section = page.getByRole("region", { name: "Browsers are not told to always use HTTPS" });
  await section.getByRole("tab", { name: "Apache" }).focus();
  await page.keyboard.press("ArrowRight");
  await expect(section.getByRole("tab", { name: "Nginx" })).toBeFocused();
  await expect(section.getByRole("tab", { name: "Nginx" })).toHaveAttribute("aria-selected", "true");
});

test("a second check shows the progress, only after the visitor opted in", async ({ page }) => {
  await simulateApi(page, [makeReport("first"), makeReport("improved")]);
  await page.goto("/en");
  await checkWebsite(page);

  expect(await page.evaluate(() => window.localStorage.length)).toBe(0);
  await page.getByRole("button", { name: t.progress.remember }).click();
  await expect(page.getByText(t.progress.remembered)).toBeVisible();

  await page.getByRole("button", { name: t.report.newCheck }).click();
  await checkWebsite(page);

  const progress = page.getByRole("region", { name: t.progress.title });
  await expect(progress).toBeVisible();
  await expect(progress.getByText("70 → 90")).toBeVisible();
  await expect(progress.getByRole("heading", { name: t.progress.fixed(1) })).toBeVisible();
  await expect(progress.getByText("Your Git folder can be downloaded by anyone")).toBeVisible();
  await expectAccessible(page);
  if (process.env.E2E_SCREENSHOTS) {
    await progress.screenshot({ path: `test-results/progress-${test.info().project.name}.png` });
  }

  await progress.getByRole("button", { name: t.progress.forget }).click();
  await expect(progress.getByText(t.progress.forgotten)).toBeVisible();
  expect(await page.evaluate(() => window.localStorage.length)).toBe(0);
});

test("the report reads right to left in Arabic", async ({ page }) => {
  await simulateApi(page, [makeReport("first")]);
  await page.goto("/ar");
  const ar = MESSAGES.ar;
  await page.getByLabel(ar.form.urlLabel).fill("shop.example");
  await page.getByLabel(ar.form.authorize).check();
  await page.getByRole("button", { name: ar.form.submit }).click();
  await expect(page.getByRole("heading", { level: 1, name: ar.report.title })).toBeVisible();
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
  await expectAccessible(page);
});
