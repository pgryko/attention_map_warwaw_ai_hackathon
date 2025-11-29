import { Marker, Popup } from "react-leaflet";
import L from "leaflet";

// Severity colors
const SEVERITY_COLORS = {
  1: "#22c55e", // green
  2: "#eab308", // yellow
  3: "#f97316", // orange
  4: "#ef4444", // red
};

// Category icons (emoji for simplicity)
const CATEGORY_ICONS = {
  emergency: "fire",
  security: "shield",
  traffic: "car",
  protest: "users",
  infrastructure: "tool",
  environmental: "tree",
  informational: "info",
};

/**
 * Create a custom divIcon for the marker.
 */
function createMarkerIcon(severity, isSelected) {
  const color = SEVERITY_COLORS[severity] || SEVERITY_COLORS[1];
  const size = isSelected ? 40 : 30;
  const borderColor = isSelected ? "#1d4ed8" : "#fff";

  return L.divIcon({
    className: "custom-marker",
    html: `
      <div style="
        width: ${size}px;
        height: ${size}px;
        background-color: ${color};
        border: 3px solid ${borderColor};
        border-radius: 50%;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        ${severity === 4 ? "animation: pulse 2s infinite;" : ""}
      "></div>
    `,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
}

export default function EventMarker({ event, isSelected, onClick }) {
  const icon = createMarkerIcon(event.severity, isSelected);

  return (
    <Marker
      position={[event.latitude, event.longitude]}
      icon={icon}
      eventHandlers={{
        click: onClick,
      }}
    >
      <Popup>
        <div className="min-w-48">
          <div className="font-semibold text-gray-900 capitalize">
            {event.category || "Unclassified"}
          </div>
          <div className="text-sm text-gray-500">
            Severity: {event.severity} / 4
          </div>
          <div className="text-sm text-gray-500">Status: {event.status}</div>
          {event.description && (
            <div className="mt-2 text-sm text-gray-700">
              {event.description}
            </div>
          )}
        </div>
      </Popup>
    </Marker>
  );
}
