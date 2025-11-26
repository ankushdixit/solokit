import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test.describe("Home Page", () => {
  test("should load the home page", async ({ page }) => {
    await page.goto("/");

    // Check for the main heading
    await expect(page.getByRole("heading", { name: /full-stack.*next\.js/i })).toBeVisible();
  });

  test("should display example component", async ({ page }) => {
    await page.goto("/");

    // Wait for the example component to load
    await expect(page.getByText(/client component example/i)).toBeVisible();
    await expect(page.getByText(/count:/i)).toBeVisible();
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

    // Check that both cards are visible using more reliable selectors
    await expect(page.getByRole("heading", { name: /api routes/i })).toBeVisible();
    await expect(page.getByRole("heading", { name: /database/i })).toBeVisible();
  });

  test("should have working increment button", async ({ page }) => {
    await page.goto("/");

    // Find and click the increment button
    const button = page.getByRole("button", { name: /increment/i });
    await expect(button).toBeVisible();

    // Initial count should be 0
    await expect(page.getByText(/count: 0/i)).toBeVisible();

    // Click the button
    await button.click();

    // Count should now be 1
    await expect(page.getByText(/count: 1/i)).toBeVisible();
  });
});
