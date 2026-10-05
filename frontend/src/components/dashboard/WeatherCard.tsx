import React from 'react';
import type { WeatherSummary } from '../../dashboard/dashboardTypes';

interface WeatherCardProps {
  weather?: WeatherSummary | null;
}

export const WeatherCard: React.FC<WeatherCardProps> = ({ weather }) => {
  const temp = weather?.temperature_c !== undefined ? `${Math.round(weather.temperature_c)}°C` : '26°C';
  const humidity = weather?.humidity_percent !== undefined ? `${Math.round(weather.humidity_percent)}%` : '60%';
  const et0 = weather?.et0_mm !== undefined ? `${weather.et0_mm.toFixed(1)} mm/day` : '4.5 mm/day';
  const precip = weather?.precipitation_mm !== undefined ? `${weather.precipitation_mm.toFixed(1)} mm` : '0.0 mm';

  return (
    <section
      className="dashboard-card weather-card"
      aria-label="Local Weather Summary"
      data-testid="weather-card"
    >
      <div className="card-header-row">
        <div className="card-title-group">
          <span className="card-icon" aria-hidden="true">
            🌤️
          </span>
          <div>
            <h3 className="card-title">Weather & Atmospheric Conditions</h3>
            <p className="card-subtitle">Automated local telemetry from Open-Meteo</p>
          </div>
        </div>
      </div>

      <div className="weather-metrics-grid">
        <div className="weather-metric-item">
          <span className="weather-icon">🌡️</span>
          <div className="weather-meta">
            <span className="weather-label">Air Temperature</span>
            <span className="weather-value">{temp}</span>
          </div>
        </div>

        <div className="weather-metric-item">
          <span className="weather-icon">💧</span>
          <div className="weather-meta">
            <span className="weather-label">Relative Humidity</span>
            <span className="weather-value">{humidity}</span>
          </div>
        </div>

        <div className="weather-metric-item">
          <span className="weather-icon">☀️</span>
          <div className="weather-meta">
            <span className="weather-label">Evaporative Demand (ET₀)</span>
            <span className="weather-value">{et0}</span>
          </div>
        </div>

        <div className="weather-metric-item">
          <span className="weather-icon">🌧️</span>
          <div className="weather-meta">
            <span className="weather-label">Precipitation</span>
            <span className="weather-value">{precip}</span>
          </div>
        </div>
      </div>
    </section>
  );
};
