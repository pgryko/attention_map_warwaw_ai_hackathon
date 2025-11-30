import { useState, useCallback } from "react";
import { MapContainer, TileLayer, useMap, Circle } from "react-leaflet";
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

/**
 * Custom control to center map on user's location.
 */
function LocationControl({ onLocationFound }) {
  const map = useMap();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleClick = useCallback(() => {
    if (!navigator.geolocation) {
      setError("Geolocation not supported");
      return;
    }

    setLoading(true);
    setError(null);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        map.flyTo([latitude, longitude], 15, { duration: 1 });
        onLocationFound?.({ latitude, longitude });
        setLoading(false);
      },
      (err) => {
        setError("Could not get location");
        setLoading(false);
        // Fall back to default center
        map.flyTo(DEFAULT_CENTER, DEFAULT_ZOOM, { duration: 1 });
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  }, [map, onLocationFound]);

  return (
    <div className="leaflet-top leaflet-right" style={{ marginTop: "10px", marginRight: "10px" }}>
      <div className="leaflet-control">
        <button
          onClick={handleClick}
          disabled={loading}
          className="flex h-8 w-8 items-center justify-center rounded-md bg-white shadow-md transition-colors hover:bg-gray-100 disabled:opacity-50 dark:bg-gray-800 dark:hover:bg-gray-700"
          title={error || "Center on my location"}
        >
          {loading ? (
            <svg className="h-4 w-4 animate-spin text-blue-600" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          ) : (
            <svg
              className={`h-4 w-4 ${error ? "text-red-500" : "text-blue-600"}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
              />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          )}
        </button>
      </div>
    </div>
  );
}

export default function EventMap({ events, selectedEvent, onEventSelect }) {
  const [userLocation, setUserLocation] = useState(null);

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

      {/* User location indicator */}
      {userLocation && (
        <Circle
          center={[userLocation.latitude, userLocation.longitude]}
          radius={50}
          pathOptions={{
            color: "#3b82f6",
            fillColor: "#3b82f6",
            fillOpacity: 0.3,
          }}
        />
      )}

      {/* Fit bounds when events change */}
      {events.length > 0 && <MapBounds events={events} />}

      {/* Location control */}
      <LocationControl onLocationFound={setUserLocation} />
    </MapContainer>
  );
}
