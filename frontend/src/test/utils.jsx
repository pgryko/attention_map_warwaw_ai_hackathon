import { render } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, MemoryRouter } from "react-router-dom";
import { AuthProvider } from "../context/AuthContext";
import { ThemeProvider } from "../context/ThemeContext";

// Create a fresh QueryClient for each test
function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
        staleTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

// All providers wrapper
function AllProviders({ children, initialEntries = ["/"] }) {
  const queryClient = createTestQueryClient();

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <MemoryRouter initialEntries={initialEntries}>
            {children}
          </MemoryRouter>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

// Custom render with all providers
export function renderWithProviders(ui, options = {}) {
  const { initialEntries = ["/"], ...renderOptions } = options;

  return render(ui, {
    wrapper: ({ children }) => (
      <AllProviders initialEntries={initialEntries}>{children}</AllProviders>
    ),
    ...renderOptions,
  });
}

// Render with QueryClient only (for component tests without routing)
export function renderWithQuery(ui, options = {}) {
  const queryClient = createTestQueryClient();

  return render(ui, {
    wrapper: ({ children }) => (
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>{children}</ThemeProvider>
      </QueryClientProvider>
    ),
    ...options,
  });
}

// Simulate logged in state
export function mockLoggedIn() {
  localStorage.getItem.mockImplementation((key) => {
    if (key === "access_token") return "mock-access-token";
    if (key === "refresh_token") return "mock-refresh-token";
    return null;
  });
}

// Simulate staff logged in state
export function mockStaffLoggedIn() {
  localStorage.getItem.mockImplementation((key) => {
    if (key === "access_token") return "mock-staff-access-token";
    if (key === "refresh_token") return "mock-staff-refresh-token";
    return null;
  });
}

// Simulate logged out state
export function mockLoggedOut() {
  localStorage.getItem.mockReturnValue(null);
}

// Wait for loading to finish
export async function waitForLoadingToFinish() {
  // Small delay to allow React Query to process
  await new Promise((resolve) => setTimeout(resolve, 0));
}

// Re-export everything from testing-library
export * from "@testing-library/react";
export { default as userEvent } from "@testing-library/user-event";
