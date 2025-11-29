import { MapContainer, TileLayer, useMap } from "react-leaflet";
import L from "leaflet";
import EventMarker from "./EventMarker";

// Default center (Warsaw)
const DEFAULT_CENTER = [52.2297, 21.0122];
const DEFAULT_ZOOM = 12;

/**
 * Component to fit map bounds to events.
 */
function MapBounds({ events }) {
  const map = useMap();

  if (events.length > 0) {
    const bounds = L.latLngBounds(events.map((e) => [e.latitude, e.longitude]));
    map.fitBounds(bounds, { padding: [50, 50], maxZoom: 15 });
  }

  return null;
}

export default function EventMap({ events, selectedEvent, onEventSelect }) {
  return (
    <MapContainer
      center={DEFAULT_CENTER}
      zoom={DEFAULT_ZOOM}
      className="h-full w-full"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {/* Event Markers */}
      {events.map((event) => (
        <EventMarker
          key={event.id}
          event={event}
          isSelected={selectedEvent?.id === event.id}
          onClick={() => onEventSelect(event)}
        />
      ))}

      {/* Fit bounds when events change */}
      {events.length > 0 && <MapBounds events={events} />}
    </MapContainer>
  );
}
