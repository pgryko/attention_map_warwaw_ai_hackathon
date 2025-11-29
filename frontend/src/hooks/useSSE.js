import { useEffect, useRef, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { createEventStream } from "../api/client";
import { QUERY_KEYS } from "../lib/constants";

/**
 * Hook to connect to SSE stream and automatically invalidate queries on updates.
 */
export function useSSE({ enabled = true } = {}) {
  const queryClient = useQueryClient();
  const eventSourceRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  const handleEvent = useCallback(
    (data) => {
      switch (data.type) {
        case "event_created":
          // Invalidate events list and stats
          queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.events] });
          queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.stats] });
          queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.clusters] });
          break;

        case "event_updated":
          // Invalidate specific event and lists
          if (data.event?.id) {
            queryClient.invalidateQueries({
              queryKey: [QUERY_KEYS.event, String(data.event.id)],
            });
          }
          queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.events] });
          queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.stats] });
          break;

        case "cluster_updated":
          queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.clusters] });
          break;

        default:
          console.log("Unknown SSE event type:", data.type);
      }
    },
    [queryClient],
  );

  const handleError = useCallback(() => {
    // Attempt to reconnect after 5 seconds
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    reconnectTimeoutRef.current = setTimeout(() => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = createEventStream(handleEvent, handleError);
      }
    }, 5000);
  }, [handleEvent]);

  useEffect(() => {
    if (!enabled) {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      return;
    }

    // Connect to SSE
    eventSourceRef.current = createEventStream(handleEvent, handleError);

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [enabled, handleEvent, handleError]);

  return {
    isConnected: !!eventSourceRef.current,
  };
}
