/**
 * API client for Attention Map backend.
 */

const API_BASE = import.meta.env.VITE_API_URL || "";

/**
 * Fetch wrapper with error handling.
 */
async function fetchApi(endpoint, options = {}) {
  const url = `${API_BASE}/api/v1${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Upload an event with media.
 */
export async function uploadEvent(formData) {
  const url = `${API_BASE}/api/v1/events/upload`;

  const response = await fetch(url, {
    method: "POST",
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
export async function updateEventStatus(eventId, status) {
  return fetchApi(`/events/${eventId}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
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
  const url = `${API_BASE}/api/v1/events/stream`;
  const eventSource = new EventSource(url);

  eventSource.addEventListener("connected", () => {
    console.log("SSE connected");
  });

  eventSource.addEventListener("event_update", (e) => {
    try {
      const data = JSON.parse(e.data);
      onEvent(data);
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
