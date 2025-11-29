import { test, expect } from "@playwright/test";

// Use desktop viewport (Recent Events section is hidden on mobile)
test.use({ viewport: { width: 1280, height: 720 } });

test.describe("Dashboard", () => {
  test("loads dashboard with stats widgets", async ({ page }) => {
    await page.goto("/");

    // Wait for stats to load (skeleton disappears, stats appear)
    // Stats labels are in paragraph elements within the stats bar
    await expect(
      page.getByRole("paragraph").filter({ hasText: "Total" }),
    ).toBeVisible({ timeout: 10000 });
    await expect(
      page.getByRole("paragraph").filter({ hasText: "New" }),
    ).toBeVisible();
    await expect(
      page.getByRole("paragraph").filter({ hasText: "Verified" }),
    ).toBeVisible();
    await expect(
      page.getByRole("paragraph").filter({ hasText: "Critical" }),
    ).toBeVisible();
    await expect(
      page.getByRole("paragraph").filter({ hasText: "Clusters" }),
    ).toBeVisible();
  });

  test("shows filter dropdowns", async ({ page }) => {
    await page.goto("/");

    // Wait for page to load
    await page.waitForLoadState("networkidle");

    // Filter bar should have 3 dropdowns (category, status, severity)
    const comboboxes = page.getByRole("combobox");
    await expect(comboboxes).toHaveCount(3);

    // Verify each dropdown has default "All" option selected
    await expect(comboboxes.nth(0)).toHaveValue(""); // All Categories
    await expect(comboboxes.nth(1)).toHaveValue(""); // All Statuses
    await expect(comboboxes.nth(2)).toHaveValue(""); // All Severities
  });

  test("shows map component", async ({ page }) => {
    await page.goto("/");

    // Map should be rendered (Leaflet attribution is visible)
    await expect(page.getByRole("link", { name: /Leaflet/i })).toBeVisible({
      timeout: 10000,
    });
    await expect(page.getByRole("button", { name: "Zoom in" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Zoom out" })).toBeVisible();
  });

  test("shows recent events section", async ({ page }) => {
    await page.goto("/");

    // Wait for page to load (Recent Events section only visible on desktop)
    await page.waitForLoadState("networkidle");

    await expect(
      page.getByRole("heading", { name: "Recent Events" }),
    ).toBeVisible();
    await expect(page.getByRole("link", { name: "+ Report" })).toBeVisible();
  });

  test("can navigate to report page from dashboard", async ({ page }) => {
    await page.goto("/");

    // Wait for sidebar to load
    await page.waitForLoadState("networkidle");

    await page.getByRole("link", { name: "+ Report" }).click();

    await expect(page).toHaveURL("/upload");
  });

  test("can filter events by category", async ({ page }) => {
    await page.goto("/");

    // Wait for filter bar to be ready
    await page.waitForLoadState("networkidle");

    // Select a category filter
    const categoryDropdown = page.getByRole("combobox").first();
    await categoryDropdown.selectOption("fire");

    // The filter should be applied (URL might change or events reload)
    await expect(categoryDropdown).toHaveValue("fire");
  });
});
