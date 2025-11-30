import { useState, useEffect, useCallback } from "react";

// Default location: Warsaw city center
const DEFAULT_LOCATION = {
  latitude: 52.2297,
  longitude: 21.0122,
};

/**
 * Hook for getting user's current location with manual fallback support.
 */
export function useGeolocation() {
  const [location, setLocation] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isManual, setIsManual] = useState(false);

  useEffect(() => {
    if (!navigator.geolocation) {
      setError("Geolocation is not supported by your browser");
      setLoading(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocation({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        });
        setLoading(false);
      },
      (err) => {
        setError(err.message);
        setLoading(false);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0,
      },
    );
  }, []);

  /**
   * Manually set location (for fallback when geolocation fails)
   */
  const setManualLocation = useCallback((lat, lng) => {
    const latitude = parseFloat(lat);
    const longitude = parseFloat(lng);

    if (isNaN(latitude) || isNaN(longitude)) {
      return false;
    }

    if (latitude < -90 || latitude > 90 || longitude < -180 || longitude > 180) {
      return false;
    }

    setLocation({ latitude, longitude });
    setIsManual(true);
    setError(null);
    return true;
  }, []);

  /**
   * Use default location (Warsaw)
   */
  const useDefaultLocation = useCallback(() => {
    setLocation(DEFAULT_LOCATION);
    setIsManual(true);
    setError(null);
  }, []);

  /**
   * Retry getting geolocation
   */
  const retryGeolocation = useCallback(() => {
    if (!navigator.geolocation) {
      return;
    }

    setLoading(true);
    setError(null);
    setIsManual(false);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocation({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        });
        setLoading(false);
      },
      (err) => {
        setError(err.message);
        setLoading(false);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0,
      },
    );
  }, []);

  return {
    location,
    error,
    loading,
    isManual,
    setManualLocation,
    useDefaultLocation,
    retryGeolocation,
  };
}
