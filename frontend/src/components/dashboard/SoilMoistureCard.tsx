import React from 'react';
import type { DashboardRecommendation } from '../../dashboard/dashboardTypes';

interface SoilMoistureCardProps {
  recommendation: DashboardRecommendation;
}

export const SoilMoistureCard: React.FC<SoilMoistureCardProps> = ({
  recommendation,
}) => {
  const currentMoisture = recommendation.current_moisture;
  const predictedMoisture = recommendation.predicted_moisture_24h;
  const fc = recommendation.field_capacity;
  const mad = recommendation.mad_threshold;

  const currentDisplay =
    currentMoisture !== null && currentMoisture !== undefined
      ? `${currentMoisture.toFixed(1)}%`
      : 'Unavailable';

  const predictedDisplay =
    predictedMoisture !== null && predictedMoisture !== undefined
      ? `${predictedMoisture.toFixed(1)}%`
      : 'Unavailable';

  const trendDelta =
    currentMoisture !== null &&
    currentMoisture !== undefined &&
    predictedMoisture !== null &&
    predictedMoisture !== undefined
      ? (predictedMoisture - currentMoisture).toFixed(1)
      : null;

  return (
    <section
      className="dashboard-card soil-moisture-card"
      aria-label="Soil Moisture Status"
      data-testid="soil-moisture-card"
    >
      <div className="card-header-row">
        <div className="card-title-group">
          <span className="card-icon" aria-hidden="true">
            🌱
          </span>
          <div>
            <h3 className="card-title">Soil Moisture</h3>
            <p className="card-subtitle">
              Active root-zone volumetric water content (% VWC)
            </p>
          </div>
        </div>
        {recommendation.moisture_state && (
          <span className="moisture-state-badge">
            State: {recommendation.moisture_state.replace('_', ' ')}
          </span>
        )}
      </div>

      <div className="moisture-metrics-grid">
        {/* Current Moisture */}
        <div className="metric-box metric-current">
          <span className="metric-label">Current root-zone moisture</span>
          <div className="metric-value-row">
            <span className="metric-primary-value">{currentDisplay}</span>
            <span className="metric-unit">VWC</span>
          </div>
          <span className="metric-caption">Measured root-zone moisture</span>
        </div>

        {/* Predicted 24h Moisture */}
        <div className="metric-box metric-predicted">
          <span className="metric-label">Expected in 24 hours</span>
          <div className="metric-value-row">
            <span className="metric-primary-value">{predictedDisplay}</span>
            <span className="metric-unit">VWC</span>
          </div>
          <span className="metric-caption">
            {trendDelta !== null ? (
              Number(trendDelta) <= 0 ? (
                <span className="trend-down">↓ {Math.abs(Number(trendDelta))}% 24h drop</span>
              ) : (
                <span className="trend-up">↑ +{trendDelta}% 24h gain</span>
              )
            ) : (
              'Forecast for next 24h'
            )}
          </span>
        </div>
      </div>

      {/* Agronomic Reference Thresholds (if available) */}
      {(fc !== null || mad !== null) && (
        <div className="soil-thresholds-bar">
          <div className="threshold-item">
            <span className="thresh-label">Allowable Depletion Line (MAD):</span>
            <span className="thresh-val">
              {mad !== null && mad !== undefined ? `${mad.toFixed(1)}% VWC` : 'N/A'}
            </span>
          </div>
          <span className="thresh-sep">&bull;</span>
          <div className="threshold-item">
            <span className="thresh-label">Field Capacity (FC):</span>
            <span className="thresh-val">
              {fc !== null && fc !== undefined ? `${fc.toFixed(1)}% VWC` : 'N/A'}
            </span>
          </div>
        </div>
      )}
    </section>
  );
};
