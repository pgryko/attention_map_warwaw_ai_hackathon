import { useQuery } from "@tanstack/react-query";
import { listEvents, getEvent, listClusters, getStats } from "../api/client";
import { QUERY_KEYS } from "../lib/constants";

/**
 * Hook to fetch events list with filters.
 */
export function useEvents(filters = {}) {
  return useQuery({
    queryKey: [QUERY_KEYS.events, filters],
    queryFn: () => listEvents(filters),
    staleTime: 30000, // 30 seconds
  });
}

/**
 * Hook to fetch a single event.
 */
export function useEvent(eventId) {
  return useQuery({
    queryKey: [QUERY_KEYS.event, eventId],
    queryFn: () => getEvent(eventId),
    enabled: !!eventId,
  });
}

/**
 * Hook to fetch clusters for the map.
 */
export function useClusters(bounds) {
  return useQuery({
    queryKey: [QUERY_KEYS.clusters, bounds],
    queryFn: () => listClusters(bounds),
    staleTime: 30000,
  });
}

/**
 * Hook to fetch dashboard statistics.
 */
export function useStats() {
  return useQuery({
    queryKey: [QUERY_KEYS.stats],
    queryFn: getStats,
    staleTime: 60000, // 1 minute
  });
}
