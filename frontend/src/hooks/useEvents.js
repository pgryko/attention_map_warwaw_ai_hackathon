import { useState, useEffect, useCallback } from "react";
import { listEvents, createEventStream } from "../api/client";

/**
 * Hook for managing events state with real-time updates.
 */
export function useEvents(initialFilters = {}) {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState(initialFilters);

  // Fetch events
  const fetchEvents = useCallback(async () => {
    try {
      setLoading(true);
      const data = await listEvents(filters);
      setEvents(data.events);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  // Initial fetch
  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  // Real-time updates via SSE
  useEffect(() => {
    const eventSource = createEventStream(
      (data) => {
        if (data.type === "new_event") {
          setEvents((prev) => [data.event, ...prev]);
        } else if (data.type === "status_change") {
          setEvents((prev) =>
            prev.map((e) => (e.id === data.event.id ? data.event : e)),
          );
        }
      },
      (err) => {
        console.error("SSE error:", err);
      },
    );

    return () => {
      eventSource.close();
    };
  }, []);

  return {
    events,
    loading,
    error,
    filters,
    setFilters,
    refetch: fetchEvents,
  };
}
