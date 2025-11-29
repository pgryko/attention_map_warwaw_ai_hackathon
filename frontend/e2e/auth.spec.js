import { test, expect } from "@playwright/test";

test.describe("Authentication", () => {
  test.beforeEach(async ({ page }) => {
    // Clear any stored tokens
    await page.goto("/");
    await page.evaluate(() => localStorage.clear());
  });

  test("shows login and signup buttons when not authenticated", async ({
    page,
  }) => {
    await page.goto("/");

    await expect(page.getByRole("link", { name: "Login" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Sign Up" })).toBeVisible();
  });

  test("can navigate to registration page", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("link", { name: "Sign Up" }).click();

    await expect(page).toHaveURL("/register");
    await expect(
      page.getByRole("heading", { name: "Create Account" }),
    ).toBeVisible();
  });

  test("can register a new user", async ({ page }) => {
    // Generate unique email to avoid conflicts
    const uniqueEmail = `testuser${Date.now()}@example.com`;

    await page.goto("/register");

    // Fill registration form
    await page
      .getByRole("textbox", { name: "you@example.com" })
      .fill(uniqueEmail);
    await page
      .getByRole("textbox", { name: "At least 8 characters" })
      .fill("TestPassword123");
    await page
      .getByRole("textbox", { name: "Confirm your password" })
      .fill("TestPassword123");

    // Submit
    await page.getByRole("button", { name: "Create Account" }).click();

    // Should redirect to dashboard and show logged-in state
    await expect(page).toHaveURL("/");
    await expect(page.getByRole("button", { name: "Logout" })).toBeVisible();
  });

  test("can navigate to login page", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("link", { name: "Login" }).click();

    await expect(page).toHaveURL("/login");
    await expect(
      page.getByRole("heading", { name: "Welcome Back" }),
    ).toBeVisible();
  });

  test("shows validation error for password mismatch", async ({ page }) => {
    await page.goto("/register");

    await page
      .getByRole("textbox", { name: "you@example.com" })
      .fill("test@example.com");
    await page
      .getByRole("textbox", { name: "At least 8 characters" })
      .fill("Password123");
    await page
      .getByRole("textbox", { name: "Confirm your password" })
      .fill("DifferentPass");

    await page.getByRole("button", { name: "Create Account" }).click();

    // Should show error message
    await expect(page.getByText(/passwords do not match/i)).toBeVisible();
  });

  test("shows validation error for short password", async ({ page }) => {
    await page.goto("/register");

    await page
      .getByRole("textbox", { name: "you@example.com" })
      .fill("test@example.com");
    await page
      .getByRole("textbox", { name: "At least 8 characters" })
      .fill("short");
    await page
      .getByRole("textbox", { name: "Confirm your password" })
      .fill("short");

    await page.getByRole("button", { name: "Create Account" }).click();

    // Should show error message
    await expect(page.getByText(/at least 8 characters/i)).toBeVisible();
  });
});
