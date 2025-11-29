import { formatDistanceToNow } from "../../utils/date";

const SEVERITY_COLORS = {
  1: "bg-green-100 text-green-800",
  2: "bg-yellow-100 text-yellow-800",
  3: "bg-orange-100 text-orange-800",
  4: "bg-red-100 text-red-800",
};

const STATUS_COLORS = {
  new: "bg-blue-100 text-blue-800",
  reviewing: "bg-purple-100 text-purple-800",
  verified: "bg-green-100 text-green-800",
  resolved: "bg-gray-100 text-gray-800",
  false_alarm: "bg-gray-100 text-gray-500",
};

export default function EventFeed({ events, selectedEvent, onEventSelect }) {
  if (events.length === 0) {
    return (
      <div className="p-8 text-center text-gray-500">
        <p>No events to display</p>
      </div>
    );
  }

  return (
    <div className="divide-y">
      {events.map((event) => (
        <div
          key={event.id}
          className={`p-4 cursor-pointer hover:bg-gray-50 transition ${
            selectedEvent?.id === event.id
              ? "bg-blue-50 border-l-4 border-blue-600"
              : ""
          }`}
          onClick={() => onEventSelect(event)}
        >
          {/* Header */}
          <div className="flex items-center justify-between mb-2">
            <span className="font-medium text-gray-900 capitalize">
              {event.category || "Unclassified"}
            </span>
            <span
              className={`px-2 py-0.5 rounded text-xs font-medium ${
                SEVERITY_COLORS[event.severity]
              }`}
            >
              Severity {event.severity}
            </span>
          </div>

          {/* Description */}
          {event.description && (
            <p className="text-sm text-gray-600 mb-2 line-clamp-2">
              {event.description}
            </p>
          )}

          {/* Footer */}
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span
              className={`px-2 py-0.5 rounded ${STATUS_COLORS[event.status]}`}
            >
              {event.status}
            </span>
            <span>{formatDistanceToNow(event.created_at)}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
