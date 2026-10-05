import React, { useEffect, useRef, useState, useCallback } from 'react';
import type { LocationData } from '../../types/assessment';
import { loadGoogleMapsScript } from '../../services/googleMapsLoader';

interface GoogleMapLocationPickerProps {
  selectedLocation: LocationData;
  onLocationChange: (loc: { latitude: number; longitude: number; place_name: string; location_confirmed: boolean }) => void;
  onConfirmLocation: (loc: { latitude: number; longitude: number; place_name: string }) => void;
}

// Helper to format reverse-geocoded place names into farmer-friendly "Village/Town, District, State"
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function extractFarmerFriendlyPlaceName(geocoderResult: any, fallbackLat: number, fallbackLng: number): string {
  if (!geocoderResult) {
    return `Farm Plot (${fallbackLat.toFixed(4)}° N, ${fallbackLng.toFixed(4)}° E)`;
  }

  const components = geocoderResult.address_components || [];
  let locality = '';
  let sublocality = '';
  let district = '';
  let state = '';

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  components.forEach((c: any) => {
    if (c.types.includes('sublocality_level_1') || c.types.includes('sublocality')) {
      sublocality = c.long_name;
    } else if (c.types.includes('locality')) {
      locality = c.long_name;
    } else if (c.types.includes('administrative_area_level_2')) {
      district = c.long_name;
    } else if (c.types.includes('administrative_area_level_1')) {
      state = c.long_name;
    }
  });

  const townOrVillage = sublocality || locality;
  const parts = [townOrVillage, district, state].filter(Boolean);

  if (parts.length >= 2) {
    return Array.from(new Set(parts)).join(', ');
  }

  if (geocoderResult.formatted_address) {
    // Return formatted address stripped of country if possible
    return geocoderResult.formatted_address.replace(/, India$/, '').trim();
  }

  return `Farm Plot (${fallbackLat.toFixed(4)}° N, ${fallbackLng.toFixed(4)}° E)`;
}

// Development presets for quick testing when offline or without API key
const DEV_TEST_PRESETS = [
  { name: 'Baramati, Pune District, Maharashtra', lat: 18.1519, lng: 74.5770, crop: 'Sugarcane / Grapes' },
  { name: 'Nashik, Maharashtra', lat: 19.9975, lng: 73.7898, crop: 'Onion / Tomato' },
  { name: 'Ludhiana, Punjab', lat: 30.9010, lng: 75.8573, crop: 'Wheat / Paddy' },
  { name: 'Guntur, Andhra Pradesh', lat: 16.3067, lng: 80.4365, crop: 'Chilli / Cotton' },
];

export const GoogleMapLocationPicker: React.FC<GoogleMapLocationPickerProps> = ({
  selectedLocation,
  onLocationChange,
  onConfirmLocation,
}) => {
  const apiKey = (import.meta.env.VITE_GOOGLE_MAPS_API_KEY || '').trim();
  const hasApiKey = Boolean(apiKey);

  // Draft coordinates & place name
  const [draftLat, setDraftLat] = useState<number>(selectedLocation.latitude || 0);
  const [draftLng, setDraftLng] = useState<number>(selectedLocation.longitude || 0);
  const [draftPlaceName, setDraftPlaceName] = useState<string>(
    selectedLocation.place_name || selectedLocation.location_name || ''
  );
  const [isConfirmed, setIsConfirmed] = useState<boolean>(selectedLocation.location_confirmed);
  const [searchAreaHint, setSearchAreaHint] = useState<string>('');

  // Map loading states
  const [mapStatus, setMapStatus] = useState<'idle' | 'loading' | 'ready' | 'error'>(
    hasApiKey ? 'loading' : 'idle'
  );
  const [mapErrorMessage, setMapErrorMessage] = useState<string>('');

  // Refs for Google Maps DOM elements and instances
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const searchInputRef = useRef<HTMLInputElement | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const mapInstanceRef = useRef<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const markerInstanceRef = useRef<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const geocoderInstanceRef = useRef<any>(null);

  // Helper to reverse geocode LatLng into human-readable place name
  const reverseGeocode = useCallback(
    (lat: number, lng: number) => {
      if (!window.google?.maps?.Geocoder) {
        const fallback = `Farm Plot (${lat.toFixed(4)}° N, ${lng.toFixed(4)}° E)`;
        setDraftPlaceName(fallback);
        onLocationChange({
          latitude: lat,
          longitude: lng,
          place_name: fallback,
          location_confirmed: false,
        });
        return;
      }

      if (!geocoderInstanceRef.current) {
        geocoderInstanceRef.current = new window.google.maps.Geocoder();
      }

      geocoderInstanceRef.current.geocode(
        { location: { lat, lng } },
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (results: any[], status: string) => {
          let resolvedName = `Farm Plot (${lat.toFixed(4)}° N, ${lng.toFixed(4)}° E)`;
          if (status === 'OK' && results && results[0]) {
            resolvedName = extractFarmerFriendlyPlaceName(results[0], lat, lng);
          }
          setDraftPlaceName(resolvedName);
          onLocationChange({
            latitude: lat,
            longitude: lng,
            place_name: resolvedName,
            location_confirmed: false,
          });
        }
      );
    },
    [onLocationChange]
  );

  // Update or create single active draggable marker
  const updateMapMarker = useCallback(
    (lat: number, lng: number, pan = true) => {
      if (!mapInstanceRef.current || !window.google?.maps) return;

      const position = { lat, lng };

      if (!markerInstanceRef.current) {
        // Create single active draggable marker
        markerInstanceRef.current = new window.google.maps.Marker({
          position,
          map: mapInstanceRef.current,
          draggable: true,
          title: 'Farm Location Pin (Drag to reposition)',
          animation: window.google.maps.Animation?.DROP,
        });

        // Add dragend listener to marker: moving marker updates coordinates & resets confirmation
        markerInstanceRef.current.addListener('dragend', () => {
          const pos = markerInstanceRef.current.getPosition();
          if (pos) {
            const newLat = Number(pos.lat().toFixed(6));
            const newLng = Number(pos.lng().toFixed(6));
            setDraftLat(newLat);
            setDraftLng(newLng);
            setIsConfirmed(false);
            reverseGeocode(newLat, newLng);
          }
        });
      } else {
        markerInstanceRef.current.setPosition(position);
      }

      if (pan) {
        mapInstanceRef.current.panTo(position);
      }
    },
    [reverseGeocode]
  );

  // Load Google Maps script when API key is present
  useEffect(() => {
    if (!hasApiKey) return;

    let isMounted = true;
    loadGoogleMapsScript(apiKey)
      .then(() => {
        if (isMounted) {
          setMapStatus('ready');
        }
      })
      .catch(() => {
        if (isMounted) {
          setMapStatus('error');
          setMapErrorMessage('Map is unavailable. Please check the Google Maps configuration.');
        }
      });

    return () => {
      isMounted = false;
    };
  }, [hasApiKey, apiKey]);

  // Initialize Map and Places Autocomplete once script is ready
  useEffect(() => {
    if (mapStatus !== 'ready' || !mapContainerRef.current || !window.google?.maps) {
      return;
    }

    const hasValidCoords = draftLat !== 0 && draftLng !== 0;
    const initialCenter = hasValidCoords
      ? { lat: draftLat, lng: draftLng }
      : { lat: 20.5937, lng: 78.9629 }; // India agricultural center default
    const initialZoom = hasValidCoords ? 15 : 5;

    // Create Map instance with mobile-friendly controls and hybrid satellite imagery
    const map = new window.google.maps.Map(mapContainerRef.current, {
      center: initialCenter,
      zoom: initialZoom,
      mapTypeId: window.google.maps.MapTypeId.HYBRID, // Satellite with labels for farmland identification
      mapTypeControl: true,
      mapTypeControlOptions: {
        style: 1, // Horizontal bar
        position: 3, // TOP_RIGHT
      },
      streetViewControl: false,
      fullscreenControl: true,
      zoomControl: true,
      gestureHandling: 'greedy', // Direct mobile touch panning
    });

    mapInstanceRef.current = map;

    // Place initial marker if coordinates are already set
    if (hasValidCoords) {
      updateMapMarker(draftLat, draftLng, false);
    }

    // Map click/tap listener: farmer taps their farm -> places or moves single active pin
    map.addListener('click', (e: { latLng?: { lat(): number; lng(): number } }) => {
      if (!e.latLng) return;
      const clickedLat = Number(e.latLng.lat().toFixed(6));
      const clickedLng = Number(e.latLng.lng().toFixed(6));
      setDraftLat(clickedLat);
      setDraftLng(clickedLng);
      setIsConfirmed(false);
      updateMapMarker(clickedLat, clickedLng, false);
      reverseGeocode(clickedLat, clickedLng);
    });

    // Initialize Places Autocomplete if search input is mounted
    if (searchInputRef.current && window.google.maps.places?.Autocomplete) {
      const autocomplete = new window.google.maps.places.Autocomplete(searchInputRef.current, {
        fields: ['formatted_address', 'geometry', 'name'],
      });

      autocomplete.addListener('place_changed', () => {
        const place = autocomplete.getPlace();
        if (!place.geometry || !place.geometry.location) {
          return;
        }

        // Section 10: Searching moves the map to that area.
        // It does NOT automatically select or confirm the farm location.
        // The farmer must still place/move the farm pin!
        map.panTo(place.geometry.location);
        map.setZoom(15);

        const areaName = place.name || place.formatted_address || 'Searched Area';
        setSearchAreaHint(`📍 Moved map to ${areaName}. Tap on your exact farm plot to place the pin.`);
      });
    }

    return () => {
      // Clean up map references on unmount
      markerInstanceRef.current = null;
      mapInstanceRef.current = null;
    };
  }, [mapStatus, draftLat, draftLng, updateMapMarker, reverseGeocode]);

  // "Use my current location" option (Section 12)
  const handleUseCurrentLocation = () => {
    if (!navigator.geolocation) {
      alert('Geolocation is not supported by your browser.');
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = Number(pos.coords.latitude.toFixed(6));
        const lng = Number(pos.coords.longitude.toFixed(6));
        setDraftLat(lat);
        setDraftLng(lng);
        setIsConfirmed(false); // Does NOT auto-confirm: farmer must still click Confirm Location

        if (mapInstanceRef.current && window.google?.maps) {
          updateMapMarker(lat, lng, true);
          mapInstanceRef.current.setZoom(16);
          reverseGeocode(lat, lng);
        } else {
          const fallback = `Current Device Location (${lat}, ${lng})`;
          setDraftPlaceName(fallback);
          onLocationChange({
            latitude: lat,
            longitude: lng,
            place_name: fallback,
            location_confirmed: false,
          });
        }
      },
      (err) => {
        // If permission denied or error, normal map workflow continues smoothly
        alert(`Could not acquire your device location: ${err.message}. You can search for your village or tap directly on the map.`);
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  // Preset button handler for development fallback
  const handleSelectDevPreset = (preset: typeof DEV_TEST_PRESETS[0]) => {
    setDraftLat(preset.lat);
    setDraftLng(preset.lng);
    setDraftPlaceName(preset.name);
    setIsConfirmed(false);

    onLocationChange({
      latitude: preset.lat,
      longitude: preset.lng,
      place_name: preset.name,
      location_confirmed: false,
    });

    if (mapInstanceRef.current && window.google?.maps) {
      updateMapMarker(preset.lat, preset.lng, true);
      mapInstanceRef.current.setZoom(15);
    }
  };

  // Confirm selected location (Section 6: only then location_confirmed = true)
  const handleConfirmLocation = () => {
    if (!draftLat || !draftLng) {
      alert('Please place a pin on your farm before confirming.');
      return;
    }

    const placeName = draftPlaceName.trim() || `Farm (${draftLat.toFixed(4)}° N, ${draftLng.toFixed(4)}° E)`;
    onConfirmLocation({
      latitude: draftLat,
      longitude: draftLng,
      place_name: placeName,
    });
    setIsConfirmed(true);
  };

  const hasCoordinates = draftLat !== 0 && draftLng !== 0;

  return (
    <div className="google-maps-location-picker">
      {/* 1. REAL GOOGLE MAPS INTERFACE */}
      {hasApiKey && mapStatus !== 'error' && (
        <div className="google-maps-active-wrapper">
          {/* Search bar row */}
          <div className="map-search-bar-row">
            <div className="map-search-input-wrap">
              <span className="search-icon">🔍</span>
              <input
                ref={searchInputRef}
                type="text"
                className="map-search-input"
                placeholder="Search village, town, or area (e.g. Baramati, Maharashtra)..."
              />
            </div>
            <button
              type="button"
              className="gps-locate-btn"
              onClick={handleUseCurrentLocation}
              title="Use my current location"
            >
              📍 Use My Current Location
            </button>
          </div>

          {searchAreaHint && (
            <div className="search-area-hint-banner">
              <span>{searchAreaHint}</span>
              <button
                type="button"
                className="close-hint-btn"
                onClick={() => setSearchAreaHint('')}
              >
                ✕
              </button>
            </div>
          )}

          {/* Interactive Map Canvas */}
          <div className="google-maps-canvas-container">
            {mapStatus === 'loading' && (
              <div className="map-loading-overlay">
                <div className="loading-spinner" />
                <p>Loading interactive Google Satellite Map...</p>
              </div>
            )}
            <div ref={mapContainerRef} className="google-maps-div" />
          </div>
        </div>
      )}

      {/* 2. CONFIGURATION / ERROR / DEVELOPMENT FALLBACK STATE */}
      {(!hasApiKey || mapStatus === 'error') && (
        <div className="maps-integration-boundary">
          <div className="maps-key-notice-card">
            <div className="notice-header">
              <span className="notice-icon">⚠️</span>
              <h4>Map is unavailable. Please check the Google Maps configuration.</h4>
            </div>
            <p className="notice-desc">
              To enable the interactive Google Satellite Map, configure{' '}
              <code>VITE_GOOGLE_MAPS_API_KEY</code> in your <code>.env.local</code> file.
              The key requires Google Maps JavaScript API and Places API enabled in Google Cloud Console.
            </p>
            {mapErrorMessage && <p className="notice-error">{mapErrorMessage}</p>}
          </div>

          {/* Development Fallback Entry Form */}
          <div className="dev-fallback-container">
            <div className="fallback-header">
              <span className="fallback-badge">Development Fallback Location Setup</span>
              <span className="fallback-disclaimer">
                (Non-API fallback for offline development & testing. Does not simulate final Google Map)
              </span>
            </div>

            <div className="fallback-form-grid">
              <div className="fallback-input-group">
                <label htmlFor="fallback-lat">Latitude (°N):</label>
                <input
                  id="fallback-lat"
                  type="number"
                  step="0.0001"
                  className="fallback-input"
                  placeholder="e.g. 18.1519"
                  value={draftLat || ''}
                  onChange={(e) => {
                    const lat = parseFloat(e.target.value) || 0;
                    setDraftLat(lat);
                    setIsConfirmed(false);
                    onLocationChange({
                      latitude: lat,
                      longitude: draftLng,
                      place_name: draftPlaceName,
                      location_confirmed: false,
                    });
                  }}
                />
              </div>

              <div className="fallback-input-group">
                <label htmlFor="fallback-lng">Longitude (°E):</label>
                <input
                  id="fallback-lng"
                  type="number"
                  step="0.0001"
                  className="fallback-input"
                  placeholder="e.g. 74.5770"
                  value={draftLng || ''}
                  onChange={(e) => {
                    const lng = parseFloat(e.target.value) || 0;
                    setDraftLng(lng);
                    setIsConfirmed(false);
                    onLocationChange({
                      latitude: draftLat,
                      longitude: lng,
                      place_name: draftPlaceName,
                      location_confirmed: false,
                    });
                  }}
                />
              </div>

              <div className="fallback-input-group full-width">
                <label htmlFor="fallback-place">Place / Village Name:</label>
                <input
                  id="fallback-place"
                  type="text"
                  className="fallback-input"
                  placeholder="e.g. Baramati, Pune District, Maharashtra"
                  value={draftPlaceName}
                  onChange={(e) => {
                    const name = e.target.value;
                    setDraftPlaceName(name);
                    setIsConfirmed(false);
                    onLocationChange({
                      latitude: draftLat,
                      longitude: draftLng,
                      place_name: name,
                      location_confirmed: false,
                    });
                  }}
                />
              </div>
            </div>

            <div className="fallback-actions-row">
              <button
                type="button"
                className="gps-locate-btn"
                onClick={handleUseCurrentLocation}
              >
                📍 Use Device GPS Location
              </button>
            </div>

            <div className="fallback-presets-block">
              <span className="presets-label">Quick Development Test Locations:</span>
              <div className="preset-chips-row">
                {DEV_TEST_PRESETS.map((p) => (
                  <button
                    key={p.name}
                    type="button"
                    className="preset-chip-btn"
                    onClick={() => handleSelectDevPreset(p)}
                  >
                    <span>📍 {p.name}</span>
                    <small>({p.crop})</small>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 3. LOCATION CONFIRMATION AREA (Matches Section 2 UI specification) */}
      <div className="location-confirmation-card">
        <div className="loc-instruction-row">
          <span className="loc-instruction-text">
            {hasCoordinates ? '📍 Move the pin to your farm' : '👆 Tap your farm on the map to place a pin'}
          </span>
        </div>

        <div className="loc-details-row">
          <div className="loc-meta">
            <span className="loc-label">Location:</span>
            <strong className="loc-name">
              {draftPlaceName || (hasCoordinates ? `${draftLat.toFixed(4)}° N, ${draftLng.toFixed(4)}° E` : 'No location selected yet')}
            </strong>
            {hasCoordinates && (
              <span className="loc-coords">
                {draftLat.toFixed(5)}° N, {draftLng.toFixed(5)}° E
              </span>
            )}
          </div>

          <div className="loc-action">
            {isConfirmed ? (
              <div className="confirmed-badge">
                <span>✓ Location Confirmed</span>
              </div>
            ) : (
              <button
                type="button"
                className="btn btn-primary confirm-loc-btn"
                disabled={!hasCoordinates}
                onClick={handleConfirmLocation}
              >
                Confirm Location
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
