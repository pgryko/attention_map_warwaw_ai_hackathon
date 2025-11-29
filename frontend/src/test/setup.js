import "@testing-library/jest-dom";
import { cleanup } from "@testing-library/react";
import { afterEach, beforeAll, afterAll, vi } from "vitest";
import { server } from "./mocks/server";

// Mock window.matchMedia for theme tests
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, "localStorage", { value: localStorageMock });

// Mock geolocation
const geolocationMock = {
  getCurrentPosition: vi.fn((success) =>
    success({
      coords: {
        latitude: 52.2297,
        longitude: 21.0122,
        accuracy: 10,
      },
    }),
  ),
  watchPosition: vi.fn(),
  clearWatch: vi.fn(),
};
Object.defineProperty(navigator, "geolocation", { value: geolocationMock });

// Mock IntersectionObserver
class IntersectionObserverMock {
  observe = vi.fn();
  disconnect = vi.fn();
  unobserve = vi.fn();
}
Object.defineProperty(window, "IntersectionObserver", {
  writable: true,
  value: IntersectionObserverMock,
});

// Mock ResizeObserver
class ResizeObserverMock {
  observe = vi.fn();
  disconnect = vi.fn();
  unobserve = vi.fn();
}
Object.defineProperty(window, "ResizeObserver", {
  writable: true,
  value: ResizeObserverMock,
});

// Setup MSW
beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => {
  cleanup();
  server.resetHandlers();
  localStorageMock.getItem.mockReset();
  localStorageMock.setItem.mockReset();
});
afterAll(() => server.close());
