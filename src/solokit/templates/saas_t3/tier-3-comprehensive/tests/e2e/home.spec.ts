import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test.describe("Home Page", () => {
  test("should load the home page", async ({ page }) => {
    await page.goto("/");

    // Check for the main heading
    await expect(page.getByRole("heading", { name: /create.*t3.*app/i })).toBeVisible();
  });

  test("should display tRPC query result", async ({ page }) => {
    await page.goto("/");

    // Wait for the tRPC query to load
    await expect(page.getByText(/hello from trpc/i)).toBeVisible();
  });

  test("should have no accessibility violations @a11y", async ({ page }) => {
    await page.goto("/");

    // Run accessibility scan
    // Cast page to any to avoid type conflict between @playwright/test and @axe-core/playwright
    const accessibilityScanResults = await new AxeBuilder({ page } as any)
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();

    // Assert no accessibility violations
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test("should navigate between sections", async ({ page }) => {
    await page.goto("/");

    // Check that both cards are visible using more reliable selectors
    await expect(page.getByRole("heading", { name: /first steps/i })).toBeVisible();
    await expect(page.getByRole("heading", { name: /documentation/i })).toBeVisible();
  });
});
