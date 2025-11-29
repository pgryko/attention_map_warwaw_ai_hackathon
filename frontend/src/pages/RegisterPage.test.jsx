import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "../context/ThemeContext";
import { AuthProvider } from "../context/AuthContext";
import RegisterPage from "./RegisterPage";

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

describe("RegisterPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it("renders registration form after loading", async () => {
    renderWithProviders(<RegisterPage />);

    await waitFor(() => {
      expect(
        screen.getByPlaceholderText(/you@example.com/i),
      ).toBeInTheDocument();
    });
    expect(
      screen.getByPlaceholderText(/at least 8 characters/i),
    ).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText(/confirm your password/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /create account/i }),
    ).toBeInTheDocument();
  });

  it("shows link to login page", async () => {
    renderWithProviders(<RegisterPage />);

    await waitFor(() => {
      expect(screen.getByText(/already have an account/i)).toBeInTheDocument();
    });
  });

  it("has required fields", async () => {
    renderWithProviders(<RegisterPage />);

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/you@example.com/i)).toBeRequired();
    });
    expect(
      screen.getByPlaceholderText(/at least 8 characters/i),
    ).toBeRequired();
    expect(
      screen.getByPlaceholderText(/confirm your password/i),
    ).toBeRequired();
  });

  it("allows typing in form fields", async () => {
    const user = userEvent.setup();
    renderWithProviders(<RegisterPage />);

    await waitFor(() => {
      expect(
        screen.getByPlaceholderText(/you@example.com/i),
      ).toBeInTheDocument();
    });

    const emailInput = screen.getByPlaceholderText(/you@example.com/i);
    const passwordInput = screen.getByPlaceholderText(/at least 8 characters/i);
    const confirmInput = screen.getByPlaceholderText(/confirm your password/i);

    await user.type(emailInput, "new@example.com");
    await user.type(passwordInput, "password123");
    await user.type(confirmInput, "password123");

    expect(emailInput).toHaveValue("new@example.com");
    expect(passwordInput).toHaveValue("password123");
    expect(confirmInput).toHaveValue("password123");
  });
});
