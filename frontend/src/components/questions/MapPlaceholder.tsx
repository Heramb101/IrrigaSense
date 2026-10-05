import React from 'react';
import { PRESET_MOCK_LOCATIONS, type MockLocationResponse } from '../../services/mockData';

interface MapPlaceholderProps {
  selectedLocation: {
    latitude: number;
    longitude: number;
    location_name?: string;
  };
  onSelectLocation: (loc: MockLocationResponse) => void;
  interactive?: boolean;
}

export const MapPlaceholder: React.FC<MapPlaceholderProps> = ({
  selectedLocation,
  onSelectLocation,
  interactive = true,
}) => {
  const isLocationSet = selectedLocation.latitude !== 0 && selectedLocation.longitude !== 0;

  return (
    <div className="map-placeholder-container">
      <div className="map-canvas-mock">
        <div className="map-grid-overlay" />
        
        {/* Visual Map Marker */}
        <div className={`map-pin-marker ${isLocationSet ? 'visible' : ''}`}>
          <div className="pin-pulse" />
          <div className="pin-head">📍</div>
          <div className="pin-callout">
            <strong>{selectedLocation.location_name || 'Selected Farmland'}</strong>
            {isLocationSet && (
              <span>
                {selectedLocation.latitude.toFixed(4)}° N, {selectedLocation.longitude.toFixed(4)}° E
              </span>
            )}
          </div>
        </div>

        <div className="map-satellite-badge">
          <span>📡 Mock Satellite Farmland View</span>
        </div>
      </div>

      {interactive && (
        <div className="map-presets-section">
          <p className="presets-title">Tap to choose your farm location (or select a preset region):</p>
          <div className="presets-grid">
            {PRESET_MOCK_LOCATIONS.map((loc) => {
              const isSelected =
                selectedLocation.latitude === loc.latitude &&
                selectedLocation.longitude === loc.longitude;

              return (
                <button
                  key={loc.location_name}
                  type="button"
                  className={`preset-location-btn ${isSelected ? 'active' : ''}`}
                  onClick={() => onSelectLocation(loc)}
                >
                  <span className="preset-pin">📍</span>
                  <div className="preset-text">
                    <span className="preset-name">{loc.location_name}</span>
                    <span className="preset-region">{loc.region}</span>
                  </div>
                  {isSelected && <span className="preset-check">✓</span>}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
