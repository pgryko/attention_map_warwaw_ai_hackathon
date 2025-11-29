import { useState } from "react";
import { Link } from "react-router-dom";
import EventMap from "../components/Map/EventMap";
import EventFeed from "../components/Dashboard/EventFeed";
import FilterBar from "../components/Dashboard/FilterBar";
import StatsWidgets from "../components/Dashboard/StatsWidgets";
import { useEvents, useStats } from "../hooks/useEvents";
import { useSSE } from "../hooks/useSSE";
import { Button } from "../components/ui/Button";
import { EventFeedSkeleton, StatsBarSkeleton } from "../components/ui/Skeleton";
import { cn } from "../lib/utils";

export default function DashboardPage() {
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [filters, setFilters] = useState({});
  const [mobileView, setMobileView] = useState("map"); // 'map' or 'feed'

  // Enable SSE for real-time updates
  useSSE({ enabled: true });

  // Fetch data with TanStack Query
  const {
    data: eventsData,
    isLoading: eventsLoading,
    error: eventsError,
  } = useEvents(filters);

  const { data: stats, isLoading: statsLoading } = useStats();

  const events = eventsData?.events || eventsData || [];

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col">
      {/* Stats Bar */}
      {statsLoading ? (
        <StatsBarSkeleton />
      ) : (
        stats && <StatsWidgets stats={stats} />
      )}

      {/* Filter Bar */}
      <FilterBar filters={filters} onFilterChange={setFilters} />

      {/* Mobile Tab Bar */}
      <div className="flex border-b bg-white dark:border-gray-700 dark:bg-gray-800 md:hidden">
        <button
          onClick={() => setMobileView("map")}
          className={cn(
            "flex-1 py-3 text-sm font-medium transition-colors",
            mobileView === "map"
              ? "border-b-2 border-blue-600 text-blue-600 dark:text-blue-400"
              : "text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200",
          )}
        >
          <span className="mr-2">🗺️</span>
          Map
        </button>
        <button
          onClick={() => setMobileView("feed")}
          className={cn(
            "flex-1 py-3 text-sm font-medium transition-colors",
            mobileView === "feed"
              ? "border-b-2 border-blue-600 text-blue-600 dark:text-blue-400"
              : "text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200",
          )}
        >
          <span className="mr-2">📋</span>
          Feed
          {events.length > 0 && (
            <span className="ml-2 rounded-full bg-blue-100 px-2 py-0.5 text-xs dark:bg-blue-900/30">
              {events.length}
            </span>
          )}
        </button>
      </div>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Map - Desktop always visible, Mobile conditional */}
        <div
          className={cn(
            "flex-1",
            mobileView === "feed" ? "hidden md:block" : "block",
          )}
        >
          <EventMap
            events={events}
            selectedEvent={selectedEvent}
            onEventSelect={(event) => {
              setSelectedEvent(event);
              // On mobile, switch to feed when selecting an event
              if (window.innerWidth < 768) {
                setMobileView("feed");
              }
            }}
          />
        </div>

        {/* Event Feed - Mobile conditional, Desktop sidebar */}
        <div
          className={cn(
            "flex-col border-l bg-white dark:border-gray-700 dark:bg-gray-800",
            // Desktop: fixed sidebar width
            "md:flex md:w-96",
            // Mobile: full width when active
            mobileView === "feed" ? "flex w-full" : "hidden",
          )}
        >
          {/* Sidebar header - hidden on mobile (we have tabs) */}
          <div className="hidden items-center justify-between border-b px-4 py-3 dark:border-gray-700 md:flex">
            <h2 className="font-semibold text-gray-900 dark:text-white">
              Recent Events
            </h2>
            <Link to="/upload">
              <Button size="sm">+ Report</Button>
            </Link>
          </div>

          {/* Events list */}
          <div className="flex-1 overflow-y-auto">
            {eventsLoading ? (
              <EventFeedSkeleton count={5} />
            ) : eventsError ? (
              <div className="p-4 text-center text-red-500 dark:text-red-400">
                Failed to load events
              </div>
            ) : (
              <EventFeed
                events={events}
                selectedEvent={selectedEvent}
                onEventSelect={setSelectedEvent}
              />
            )}
          </div>
        </div>
      </div>

      {/* Mobile: Floating Report Button */}
      <Link
        to="/upload"
        className={cn(
          "fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-blue-600 text-white shadow-lg transition-transform hover:bg-blue-700 md:hidden",
          // Hide FAB when scrolling feed to avoid overlap with content
          mobileView === "feed" && events.length > 3 ? "translate-y-20" : "",
        )}
        aria-label="Report incident"
      >
        <svg
          className="h-6 w-6"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 4v16m8-8H4"
          />
        </svg>
      </Link>

      {/* Mobile: Bottom safe area padding when feed is shown */}
      {mobileView === "feed" && (
        <div className="h-20 flex-shrink-0 md:hidden" />
      )}
    </div>
  );
}
