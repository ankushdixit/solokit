import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test.describe("Home Page", () => {
  test("should load the home page", async ({ page }) => {
    await page.goto("/");

    // Check for the main heading
    await expect(page.getByRole("heading", { name: /welcome to.*t3/i })).toBeVisible();
  });

  test("should display getting started message", async ({ page }) => {
    await page.goto("/");

    // Check for the getting started text
    await expect(page.getByText(/your t3 stack application is ready/i)).toBeVisible();
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

  test("should show guidance about architecture", async ({ page }) => {
    await page.goto("/");

    // Check that guidance text is visible
    await expect(page.getByText(/read architecture\.md/i)).toBeVisible();
  });

  test("should show guidance about PRD", async ({ page }) => {
    await page.goto("/");

    // Check that PRD guidance is visible
    await expect(page.getByText(/create your prd/i)).toBeVisible();
  });
});
