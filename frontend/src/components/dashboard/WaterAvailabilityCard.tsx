import React from 'react';
import type { DashboardRecommendation } from '../../dashboard/dashboardTypes';

interface WaterAvailabilityCardProps {
  recommendation: DashboardRecommendation;
}

export const WaterAvailabilityCard: React.FC<WaterAvailabilityCardProps> = ({
  recommendation,
}) => {
  const waterAvailability =
    recommendation.context.water_availability || 'Moderate';
  const irrigationMethod =
    recommendation.context.irrigation_method || 'Drip';

  const isLimited =
    waterAvailability.toLowerCase().includes('limited') ||
    waterAvailability.toLowerCase().includes('scarc') ||
    waterAvailability.toLowerCase().includes('low');

  return (
    <section
      className="dashboard-card water-card"
      aria-label="Water Supply and Irrigation Method"
      data-testid="water-availability-card"
    >
      <div className="card-header-row">
        <div className="card-title-group">
          <span className="card-icon" aria-hidden="true">
            🌊
          </span>
          <div>
            <h3 className="card-title">Water Security & Delivery Method</h3>
            <p className="card-subtitle">On-farm water supply and distribution infrastructure</p>
          </div>
        </div>
      </div>

      <div className="water-info-grid">
        <div className="water-cell">
          <span className="water-label">Reported Water Availability</span>
          <span className="water-value-badge">{waterAvailability}</span>
        </div>

        <div className="water-cell">
          <span className="water-label">Irrigation System</span>
          <span className="water-value-badge">{irrigationMethod}</span>
        </div>
      </div>

      <div className="water-advisory-note">
        <span className="note-icon">{isLimited ? '⚠️' : '💡'}</span>
        <p className="note-text">
          {isLimited
            ? 'Water availability is limited. Agronomic warnings are never suppressed: if irrigation is recommended, prioritize active root zones during early morning or evening to minimize evaporative drift.'
            : 'Water availability is currently sufficient. Follow recommended depletion intervals to prevent over-saturation and nutrient leaching.'}
        </p>
      </div>
    </section>
  );
};
