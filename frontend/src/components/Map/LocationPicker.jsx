import { useState, useCallback } from "react";
import { MapContainer, TileLayer, Marker, useMapEvents, useMap } from "react-leaflet";
import L from "leaflet";

// Default center (Warsaw)
const DEFAULT_CENTER = [52.2297, 21.0122];
const DEFAULT_ZOOM = 13;

// Custom marker icon
const markerIcon = new L.Icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

/**
 * Component to handle map click events.
 */
function MapClickHandler({ onLocationSelect }) {
  useMapEvents({
    click(e) {
      onLocationSelect({
        latitude: e.latlng.lat,
        longitude: e.latlng.lng,
      });
    },
  });
  return null;
}

/**
 * Component to center map on a location.
 */
function CenterMap({ center }) {
  const map = useMap();
  if (center) {
    map.flyTo([center.latitude, center.longitude], 15, { duration: 0.5 });
  }
  return null;
}

/**
 * Location picker component with a mini-map for selecting location.
 */
export default function LocationPicker({ location, onLocationSelect, className = "" }) {
  const [showMap, setShowMap] = useState(false);

  const handleLocateMe = useCallback(() => {
    if (!navigator.geolocation) {
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        onLocationSelect({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        });
      },
      () => {
        // On error, center on default
        onLocationSelect({
          latitude: DEFAULT_CENTER[0],
          longitude: DEFAULT_CENTER[1],
        });
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  }, [onLocationSelect]);

  return (
    <div className={className}>
      {/* Toggle button */}
      <button
        type="button"
        onClick={() => setShowMap(!showMap)}
        className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
          />
        </svg>
        {showMap ? "Hide Map" : "Pick on Map"}
      </button>

      {/* Map container */}
      {showMap && (
        <div className="mt-3 overflow-hidden rounded-lg border dark:border-gray-600">
          <div className="relative h-48">
            <MapContainer
              center={location ? [location.latitude, location.longitude] : DEFAULT_CENTER}
              zoom={DEFAULT_ZOOM}
              className="h-full w-full"
              style={{ zIndex: 0 }}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />

              {/* Click handler */}
              <MapClickHandler onLocationSelect={onLocationSelect} />

              {/* Selected location marker */}
              {location && (
                <Marker
                  position={[location.latitude, location.longitude]}
                  icon={markerIcon}
                />
              )}

              {/* Center map when location changes */}
              {location && <CenterMap center={location} />}
            </MapContainer>

            {/* Locate me button */}
            <button
              type="button"
              onClick={handleLocateMe}
              className="absolute right-2 top-2 z-[1000] flex h-8 w-8 items-center justify-center rounded-md bg-white shadow-md transition-colors hover:bg-gray-100 dark:bg-gray-800 dark:hover:bg-gray-700"
              title="Use my location"
            >
              <svg className="h-4 w-4 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </button>
          </div>
          <p className="bg-gray-50 px-3 py-2 text-xs text-gray-500 dark:bg-gray-800 dark:text-gray-400">
            Click on the map to set location
          </p>
        </div>
      )}
    </div>
  );
}
