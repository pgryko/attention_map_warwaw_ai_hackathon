import { Link } from "react-router-dom";
import { formatRelativeTime } from "../../lib/utils";
import { StatusBadge } from "../ui/Badge";
import { cn } from "../../lib/utils";
import { EVENT_CATEGORIES } from "../../lib/constants";

const SEVERITY_STYLES = {
  1: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
  2: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",
  3: "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400",
  4: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
};

function EventCard({ event, isSelected, onSelect }) {
  const categoryConfig = EVENT_CATEGORIES[event.category];

  return (
    <div
      className={cn(
        "cursor-pointer border-b p-4 transition-colors",
        "hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-700/50",
        isSelected &&
          "border-l-4 border-l-blue-600 bg-blue-50 dark:bg-blue-900/20",
      )}
      onClick={() => onSelect(event)}
    >
      {/* Header row */}
      <div className="mb-2 flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          {categoryConfig && (
            <span className="text-lg" title={categoryConfig.label}>
              {categoryConfig.icon}
            </span>
          )}
          <span className="font-medium capitalize text-gray-900 dark:text-white">
            {event.category || "Unclassified"}
          </span>
        </div>
        {event.severity && (
          <span
            className={cn(
              "flex-shrink-0 rounded px-2 py-0.5 text-xs font-medium",
              SEVERITY_STYLES[event.severity],
            )}
          >
            {event.severity === 4
              ? "Critical"
              : event.severity === 3
                ? "High"
                : event.severity === 2
                  ? "Medium"
                  : "Low"}
          </span>
        )}
      </div>

      {/* Description */}
      {event.description && (
        <p className="mb-2 line-clamp-2 text-sm text-gray-600 dark:text-gray-400">
          {event.description}
        </p>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between text-xs">
        <StatusBadge status={event.status} size="sm" />
        <span className="text-gray-500 dark:text-gray-400">
          {formatRelativeTime(event.created_at)}
        </span>
      </div>

      {/* View link */}
      <Link
        to={`/event/${event.id}`}
        className="mt-2 block text-xs text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
        onClick={(e) => e.stopPropagation()}
      >
        View details →
      </Link>
    </div>
  );
}

export default function EventFeed({ events, selectedEvent, onEventSelect }) {
  if (!events || events.length === 0) {
    return (
      <div className="flex h-64 flex-col items-center justify-center p-8 text-center">
        <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900/30">
          <svg
            className="h-8 w-8 text-blue-600 dark:text-blue-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
            />
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
            />
          </svg>
        </div>
        <p className="mb-1 font-medium text-gray-700 dark:text-gray-300">
          No incidents reported yet
        </p>
        <p className="mb-4 text-sm text-gray-500 dark:text-gray-400">
          Be the first to report what's happening in your area
        </p>
        <Link
          to="/upload"
          className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Report Incident
        </Link>
      </div>
    );
  }

  return (
    <div className="divide-y dark:divide-gray-700">
      {events.map((event) => (
        <EventCard
          key={event.id}
          event={event}
          isSelected={selectedEvent?.id === event.id}
          onSelect={onEventSelect}
        />
      ))}
    </div>
  );
}
