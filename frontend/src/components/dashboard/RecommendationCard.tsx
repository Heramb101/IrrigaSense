import React from 'react';
import type { DashboardRecommendation } from '../../dashboard/dashboardTypes';
import {
  getFarmerFriendlyStatus,
  getFarmerFriendlyConfidence,
} from '../../dashboard/dashboardTypes';

interface RecommendationCardProps {
  recommendation: DashboardRecommendation;
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({
  recommendation,
}) => {
  const status = getFarmerFriendlyStatus(recommendation.decision);
  const confidence = getFarmerFriendlyConfidence(
    recommendation.confidence,
    recommendation.domain_status
  );

  return (
    <section
      className={`dashboard-card recommendation-hero-card theme-${status.theme}`}
      aria-label="Main Irrigation Recommendation"
      data-testid="recommendation-card"
    >
      <div className="recommendation-hero-header">
        <div className="status-badge-row">
          <span className={`status-pill pill-${status.theme}`}>
            <span className="status-dot" />
            {status.badgeText}
          </span>
          <span className={`confidence-pill ${confidence.badgeClass}`}>
            {confidence.label}
          </span>
        </div>

        <div className="hero-title-group">
          <span className="hero-status-icon" aria-hidden="true">
            {status.icon}
          </span>
          <div>
            <h2 className="hero-status-heading">{status.label}</h2>
            <p className="hero-crop-stage">
              Crop: <strong>{recommendation.crop}</strong>
              {recommendation.crop_stage && (
                <span> &bull; Stage: <strong>{recommendation.crop_stage}</strong></span>
              )}
              {recommendation.dap !== null && recommendation.dap !== undefined && (
                <span> &bull; Day <strong>{recommendation.dap}</strong> after planting</span>
              )}
            </p>
          </div>
        </div>
      </div>

      <div className="recommendation-body">
        <div className="recommendation-explanation-box">
          <h3 className="explanation-title">Why am I seeing this recommendation?</h3>
          <p className="explanation-text">{recommendation.reason}</p>
          {confidence.tip && (
            <p className="confidence-tip-text">
              <span className="info-icon">ℹ️</span> {confidence.tip}
            </p>
          )}
        </div>

        {recommendation.warnings && recommendation.warnings.length > 0 && (
          <div className="recommendation-warnings-alert" role="alert">
            <span className="warning-icon">⚠️</span>
            <div className="warning-content">
              <strong>Advisory Notice:</strong>
              <ul>
                {recommendation.warnings.map((warn, i) => (
                  <li key={i}>{warn}</li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    </section>
  );
};
