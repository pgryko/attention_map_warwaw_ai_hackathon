/**
 * API client for Attention Map backend.
 */
import { STORAGE_KEYS } from "../lib/constants";

const API_BASE = import.meta.env.VITE_API_URL || "";

// Token management
export function getAccessToken() {
  return localStorage.getItem(STORAGE_KEYS.accessToken);
}

export function getRefreshToken() {
  return localStorage.getItem(STORAGE_KEYS.refreshToken);
}

export function setTokens(access, refresh) {
  localStorage.setItem(STORAGE_KEYS.accessToken, access);
  if (refresh) {
    localStorage.setItem(STORAGE_KEYS.refreshToken, refresh);
  }
}

export function clearTokens() {
  localStorage.removeItem(STORAGE_KEYS.accessToken);
  localStorage.removeItem(STORAGE_KEYS.refreshToken);
}

// Refresh token logic
let refreshPromise = null;

async function refreshAccessToken() {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    throw new Error("No refresh token available");
  }

  const response = await fetch(`${API_BASE}/api/v1/token/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh: refreshToken }),
  });

  if (!response.ok) {
    clearTokens();
    throw new Error("Token refresh failed");
  }

  const data = await response.json();
  setTokens(data.access, data.refresh);
  return data.access;
}

/**
 * Fetch wrapper with auth and error handling.
 */
export async function fetchApi(endpoint, options = {}) {
  const url = `${API_BASE}/api/v1${endpoint}`;
  const { skipAuth = false, ...fetchOptions } = options;

  // Build headers
  const headers = {
    ...fetchOptions.headers,
  };

  // Add Content-Type for non-FormData requests
  if (!(fetchOptions.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  // Add auth token if available and not skipped
  if (!skipAuth) {
    const token = getAccessToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }

  let response = await fetch(url, {
    ...fetchOptions,
    headers,
  });

  // Handle 401 - try to refresh token
  if (response.status === 401 && !skipAuth && getRefreshToken()) {
    try {
      // Deduplicate refresh requests
      if (!refreshPromise) {
        refreshPromise = refreshAccessToken();
      }
      const newToken = await refreshPromise;
      refreshPromise = null;

      // Retry original request with new token
      headers["Authorization"] = `Bearer ${newToken}`;
      response = await fetch(url, {
        ...fetchOptions,
        headers,
      });
    } catch {
      refreshPromise = null;
      clearTokens();
      window.location.href = "/login";
      throw new Error("Session expired. Please log in again.");
    }
  }

  // Handle errors
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    const message =
      error.detail || error.message || `HTTP error! status: ${response.status}`;
    throw new Error(message);
  }

  // Handle empty responses
  const contentType = response.headers.get("content-type");
  if (contentType && contentType.includes("application/json")) {
    return response.json();
  }

  return response.text();
}

/**
 * Upload an event with media.
 */
export async function uploadEvent(formData) {
  const token = getAccessToken();
  const headers = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}/api/v1/events/upload`, {
    method: "POST",
    headers,
    body: formData,
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Upload failed" }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * List events with filters.
 */
export async function listEvents(params = {}) {
  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      searchParams.set(key, value);
    }
  });

  const query = searchParams.toString();
  return fetchApi(`/events${query ? `?${query}` : ""}`);
}

/**
 * Get event details.
 */
export async function getEvent(eventId) {
  return fetchApi(`/events/${eventId}`);
}

/**
 * Update event status.
 */
export async function updateEventStatus(eventId, status, notes) {
  return fetchApi(`/events/${eventId}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status, notes }),
  });
}

/**
 * List clusters.
 */
export async function listClusters(bounds) {
  const params = bounds ? `?bounds=${bounds}` : "";
  return fetchApi(`/clusters${params}`);
}

/**
 * Get dashboard stats.
 */
export async function getStats() {
  return fetchApi("/stats/summary");
}

/**
 * Create SSE connection for real-time updates.
 */
export function createEventStream(onEvent, onError) {
  const token = getAccessToken();
  const url = token
    ? `${API_BASE}/api/v1/events/stream?token=${token}`
    : `${API_BASE}/api/v1/events/stream`;

  const eventSource = new EventSource(url);

  eventSource.addEventListener("connected", () => {
    console.log("SSE connected");
  });

  eventSource.addEventListener("event_created", (e) => {
    try {
      const data = JSON.parse(e.data);
      onEvent({ type: "event_created", event: data });
    } catch (err) {
      console.error("Failed to parse SSE data:", err);
    }
  });

  eventSource.addEventListener("event_updated", (e) => {
    try {
      const data = JSON.parse(e.data);
      onEvent({ type: "event_updated", event: data });
    } catch (err) {
      console.error("Failed to parse SSE data:", err);
    }
  });

  eventSource.addEventListener("cluster_updated", (e) => {
    try {
      const data = JSON.parse(e.data);
      onEvent({ type: "cluster_updated", cluster: data });
    } catch (err) {
      console.error("Failed to parse SSE data:", err);
    }
  });

  eventSource.onerror = (err) => {
    console.error("SSE error:", err);
    if (onError) onError(err);
  };

  return eventSource;
}
