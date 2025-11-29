import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "../context/ThemeContext";
import { AuthProvider } from "../context/AuthContext";
import LoginPage from "./LoginPage";

function renderWithProviders(ui) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <BrowserRouter>{ui}</BrowserRouter>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>,
  );
}

describe("LoginPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it("renders login form after loading", async () => {
    renderWithProviders(<LoginPage />);

    await waitFor(() => {
      expect(
        screen.getByPlaceholderText(/you@example.com/i),
      ).toBeInTheDocument();
    });
    expect(
      screen.getByPlaceholderText(/enter your password/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /sign in/i }),
    ).toBeInTheDocument();
  });

  it("shows link to register page", async () => {
    renderWithProviders(<LoginPage />);

    await waitFor(() => {
      expect(screen.getByText(/don't have an account/i)).toBeInTheDocument();
    });
    expect(screen.getByRole("link", { name: /sign up/i })).toBeInTheDocument();
  });

  it("has required fields", async () => {
    renderWithProviders(<LoginPage />);

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/you@example.com/i)).toBeRequired();
    });
    expect(screen.getByPlaceholderText(/enter your password/i)).toBeRequired();
  });

  it("allows typing in form fields", async () => {
    const user = userEvent.setup();
    renderWithProviders(<LoginPage />);

    await waitFor(() => {
      expect(
        screen.getByPlaceholderText(/you@example.com/i),
      ).toBeInTheDocument();
    });

    const emailInput = screen.getByPlaceholderText(/you@example.com/i);
    const passwordInput = screen.getByPlaceholderText(/enter your password/i);

    await user.type(emailInput, "test@example.com");
    await user.type(passwordInput, "password123");

    expect(emailInput).toHaveValue("test@example.com");
    expect(passwordInput).toHaveValue("password123");
  });
});
