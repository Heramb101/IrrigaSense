import React, { useEffect, useRef, useState } from 'react';
import { loadGoogleMapsScript } from '../../services/googleMapsLoader';
import type { FarmLocationInfo } from '../../dashboard/dashboardTypes';

interface SatelliteMapCardProps {
  location: FarmLocationInfo;
}

export const SatelliteMapCard: React.FC<SatelliteMapCardProps> = ({ location }) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const markerInstanceRef = useRef<any>(null);

  const [mapState, setMapState] = useState<'loading' | 'ready' | 'fallback'>('loading');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const apiKey = (
    (typeof import.meta !== 'undefined' && import.meta.env?.VITE_GOOGLE_MAPS_API_KEY) ||
    ((globalThis as any).process?.env?.VITE_GOOGLE_MAPS_API_KEY) ||
    ''
  ).trim();


  const hasValidCoordinates =
    location.latitude !== 0 &&
    location.longitude !== 0 &&
    !isNaN(location.latitude) &&
    !isNaN(location.longitude);

  useEffect(() => {
    let isMounted = true;

    if (!hasValidCoordinates) {
      setMapState('fallback');
      setErrorMessage('Farm location coordinates not confirmed.');
      return;
    }

    if (!apiKey) {
      setMapState('fallback');
      setErrorMessage('Google Maps API key not configured (Development Fallback Active).');
      return;
    }

    const initMap = async () => {
      try {
        await loadGoogleMapsScript(apiKey);

        if (!isMounted || !mapContainerRef.current) return;

        const google = (window as any).google;
        if (!google?.maps?.Map) {
          throw new Error('Google Maps Map constructor not available.');
        }

        const centerLatLng = {
          lat: location.latitude,
          lng: location.longitude,
        };

        // Initialize map defaulting to SATELLITE view
        const map = new google.maps.Map(mapContainerRef.current, {
          center: centerLatLng,
          zoom: 16,
          mapTypeId: 'satellite',
          mapTypeControl: true,
          mapTypeControlOptions: {
            style: google.maps.MapTypeControlStyle.HORIZONTAL_BAR,
            position: google.maps.ControlPosition.TOP_RIGHT,
          },
          zoomControl: true,
          streetViewControl: false,
          fullscreenControl: true,
          gestureHandling: 'cooperative',
        });

        mapInstanceRef.current = map;

        // Place active farm marker
        const marker = new google.maps.Marker({
          position: centerLatLng,
          map,
          title: location.place_name || 'Confirmed Farm Plot',
          animation: google.maps.Animation.DROP,
        });

        markerInstanceRef.current = marker;

        if (isMounted) {
          setMapState('ready');
          setErrorMessage(null);
        }
      } catch (err: any) {
        if (isMounted) {
          console.warn('Satellite map load error:', err?.message);
          setMapState('fallback');
          setErrorMessage('Farm satellite map is unavailable. Displaying location overview.');
        }
      }
    };

    initMap();

    return () => {
      isMounted = false;
      if (markerInstanceRef.current) {
        markerInstanceRef.current.setMap(null);
        markerInstanceRef.current = null;
      }
      mapInstanceRef.current = null;
    };
  }, [apiKey, location.latitude, location.longitude, hasValidCoordinates]);

  return (
    <section
      className="dashboard-card satellite-map-card"
      aria-label="Farm Location and Satellite View"
      data-testid="satellite-map-card"
    >
      <div className="card-header-row">
        <div className="card-title-group">
          <span className="card-icon" aria-hidden="true">
            🛰️
          </span>
          <div>
            <h3 className="card-title">Farm Location & Satellite View</h3>
            <p className="card-subtitle">
              {location.place_name || 'Confirmed Farmland'} &bull; {location.latitude.toFixed(5)}° N, {location.longitude.toFixed(5)}° E
            </p>
          </div>
        </div>
        <span className="satellite-tag">Google Satellite Layer</span>
      </div>


      <div className="satellite-map-container-wrapper">
        {/* Real Google Map Container */}
        <div
          ref={mapContainerRef}
          className={`satellite-map-canvas ${mapState === 'ready' ? 'visible' : 'hidden'}`}
          style={{ minHeight: '320px', width: '100%', borderRadius: '12px' }}
        />

        {/* Fallback View (API key missing or offline) */}
        {mapState === 'fallback' && (
          <div className="satellite-fallback-card">
            <div className="fallback-satellite-visual">
              <div className="satellite-overlay-grid" />
              <div className="farm-pin-indicator">
                <span className="pin-pulse" />
                <span className="pin-marker">📍</span>
              </div>
              <span className="fallback-badge">🛰️ High-Resolution Satellite Overview</span>
            </div>
            <div className="fallback-meta">
              <span className="fallback-title">
                {location.place_name || 'Selected Farmland'}
              </span>
              <span className="fallback-coords">
                {location.latitude.toFixed(5)}° N, {location.longitude.toFixed(5)}° E
              </span>
              {errorMessage && (
                <span className="fallback-note">{errorMessage}</span>
              )}
            </div>
          </div>
        )}

        {/* Loading Indicator */}
        {mapState === 'loading' && (
          <div className="satellite-map-loading">
            <div className="loading-spinner-ring" />
            <span>Loading satellite view...</span>
          </div>
        )}
      </div>

      {/* Mandatory Physical Disclaimer */}
      <footer className="satellite-disclaimer">
        <span className="info-icon">ℹ️</span>
        <span className="disclaimer-text">
          Visual satellite overview of confirmed farm location. Satellite imagery does
          not directly measure root-zone soil moisture or NDVI.
        </span>
      </footer>
    </section>
  );
};
