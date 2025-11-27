import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

/**
 * Dashboard E2E Tests
 * Tests the main dashboard functionality and accessibility
 */

test.describe("Dashboard Page", () => {
  test("should display welcome heading", async ({ page }) => {
    await page.goto("/");

    // Check that welcome heading is visible
    await expect(
      page.getByRole("heading", { name: "Welcome to Refine Dashboard" })
    ).toBeVisible();
  });

  test("should display getting started guidance", async ({ page }) => {
    await page.goto("/");

    // Check that getting started card is visible
    await expect(page.getByText("Getting Started")).toBeVisible();
    await expect(
      page.getByText("Read ARCHITECTURE.md to understand the dashboard patterns.")
    ).toBeVisible();
  });

  test("should display next steps guidance", async ({ page }) => {
    await page.goto("/");

    // Check that next steps card is visible
    await expect(page.getByText("Next Steps")).toBeVisible();
    await expect(page.getByText("1. Set up your backend API connection")).toBeVisible();
  });

  test("should have accessible search functionality", async ({ page }) => {
    await page.goto("/");

    // Find search input by aria-label
    const searchInput = page.getByLabel("Search");
    await expect(searchInput).toBeVisible();

    // Test search input is focusable
    await searchInput.focus();
    await searchInput.fill("test query");
    await expect(searchInput).toHaveValue("test query");
  });

  test("should pass accessibility checks @a11y", async ({ page }) => {
    await page.goto("/");

    // Run accessibility scan
    // Cast page to any to avoid type conflict between @playwright/test and @axe-core/playwright
    const accessibilityScanResults = await new AxeBuilder({ page } as any)
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();

    // Assert no accessibility violations
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test("should be responsive on mobile", async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto("/");

    // Check that content is visible on mobile
    await expect(
      page.getByRole("heading", { name: "Welcome to Refine Dashboard" })
    ).toBeVisible();

    // Sidebar should be hidden on mobile
    const sidebar = page.locator("aside");
    await expect(sidebar).toBeHidden();
  });

  test("should have keyboard navigation support", async ({ page }) => {
    await page.goto("/");

    // Tab through focusable elements
    await page.keyboard.press("Tab");
    await page.keyboard.press("Tab");

    // Verify focused element is visible
    const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    expect(focusedElement).toBeTruthy();
  });
});
