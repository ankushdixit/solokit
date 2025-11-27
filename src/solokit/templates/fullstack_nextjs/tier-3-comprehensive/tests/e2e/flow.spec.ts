import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test.describe("Home Page", () => {
  test("should load the home page", async ({ page }) => {
    await page.goto("/");

    // Check for the main heading
    await expect(page.getByRole("heading", { name: /full-stack.*next\.js/i })).toBeVisible();
  });

  test("should display getting started message", async ({ page }) => {
    await page.goto("/");

    // Check for the getting started message
    await expect(page.getByText(/your project is ready/i)).toBeVisible();
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

  test("should navigate and display cards", async ({ page }) => {
    await page.goto("/");

    // Check that both cards are visible
    await expect(page.getByRole("heading", { name: /health check/i })).toBeVisible();
    await expect(page.getByRole("heading", { name: /get started/i })).toBeVisible();
  });

  test("should have link to health check", async ({ page }) => {
    await page.goto("/");

    // Find the health check link
    const link = page.getByRole("link", { name: /health check/i });
    await expect(link).toBeVisible();
    await expect(link).toHaveAttribute("href", "/api/health");
  });
});
