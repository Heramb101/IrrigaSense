import React from 'react';

interface DashboardLoadingProps {
  message?: string;
  subtext?: string;
}

export const DashboardLoading: React.FC<DashboardLoadingProps> = ({
  message = 'Preparing your irrigation recommendation...',
  subtext = 'Analyzing root-zone moisture, weather telemetry, and crop water needs...',
}) => {
  return (
    <div className="dashboard-loading-card" role="status" aria-live="polite">
      <div className="loading-spinner-wrapper">
        <div className="loading-spinner-ring" />
        <span className="loading-center-icon">💧</span>
      </div>
      <h2 className="loading-heading">{message}</h2>
      <p className="loading-subtext">{subtext}</p>
      <div className="loading-steps-indicator">
        <span className="step-pill active">1. Environmental Telemetry</span>
        <span className="step-divider">→</span>
        <span className="step-pill active">2. Soil Moisture Forecast</span>
        <span className="step-divider">→</span>
        <span className="step-pill active">3. Agronomic Decision</span>
      </div>
    </div>
  );
};
