import { test, expect } from "@playwright/test";

// Use desktop viewport for navigation tests (nav links hidden on mobile)
test.use({ viewport: { width: 1280, height: 720 } });

test.describe("Navigation", () => {
  test("shows app title in header", async ({ page }) => {
    await page.goto("/");

    await expect(
      page.getByRole("link", { name: /Attention Map/i }),
    ).toBeVisible();
  });

  test("can navigate between pages using nav links", async ({ page }) => {
    await page.goto("/");

    // Wait for page to fully load
    await page.waitForLoadState("networkidle");

    // Navigate to Report page (desktop nav - use exact match to avoid "+ Report" link)
    await page.getByRole("link", { name: "Report", exact: true }).click();
    await expect(page).toHaveURL("/upload");

    // Navigate to Leaderboard
    await page.getByRole("link", { name: "Leaderboard", exact: true }).click();
    await expect(page).toHaveURL("/leaderboard");

    // Navigate back to Dashboard
    await page.getByRole("link", { name: "Dashboard", exact: true }).click();
    await expect(page).toHaveURL("/");
  });

  test("clicking logo navigates to home", async ({ page }) => {
    await page.goto("/upload");

    await page.getByRole("link", { name: /Attention Map/i }).click();

    await expect(page).toHaveURL("/");
  });

  test("has dark mode toggle", async ({ page }) => {
    await page.goto("/");

    const themeToggle = page.getByRole("button", {
      name: /switch to dark mode/i,
    });
    await expect(themeToggle).toBeVisible();

    // Click to enable dark mode
    await themeToggle.click();

    // Should change to light mode toggle
    await expect(
      page.getByRole("button", { name: /switch to light mode/i }),
    ).toBeVisible();
  });
});
