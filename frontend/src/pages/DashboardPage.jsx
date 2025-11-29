import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import EventMap from "../components/Map/EventMap";
import EventFeed from "../components/Dashboard/EventFeed";
import FilterBar from "../components/Dashboard/FilterBar";
import StatsWidgets from "../components/Dashboard/StatsWidgets";
import { useEvents } from "../hooks/useEvents";
import { getStats } from "../api/client";

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const { events, loading, error, filters, setFilters } = useEvents();

  // Fetch stats
  useEffect(() => {
    getStats().then(setStats).catch(console.error);
  }, []);

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-sm border-b px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-bold text-gray-900">Attention Map</h1>
          <span className="text-sm text-gray-500">Operator Dashboard</span>
        </div>
        <Link
          to="/upload"
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
        >
          + Report Event
        </Link>
      </header>

      {/* Stats Bar */}
      {stats && <StatsWidgets stats={stats} />}

      {/* Filter Bar */}
      <FilterBar filters={filters} onFilterChange={setFilters} />

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Map */}
        <div className="flex-1">
          <EventMap
            events={events}
            selectedEvent={selectedEvent}
            onEventSelect={setSelectedEvent}
          />
        </div>

        {/* Event Feed Sidebar */}
        <div className="w-96 bg-white border-l overflow-y-auto">
          {loading && (
            <div className="p-4 text-center text-gray-500">
              Loading events...
            </div>
          )}
          {error && (
            <div className="p-4 text-center text-red-500">Error: {error}</div>
          )}
          {!loading && !error && (
            <EventFeed
              events={events}
              selectedEvent={selectedEvent}
              onEventSelect={setSelectedEvent}
            />
          )}
        </div>
      </div>
    </div>
  );
}
