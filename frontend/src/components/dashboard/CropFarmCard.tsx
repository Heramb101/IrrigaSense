import React from 'react';
import type { DashboardRecommendation } from '../../dashboard/dashboardTypes';

interface CropFarmCardProps {
  recommendation: DashboardRecommendation;
  plantingDate?: string;
  farmSize?: string;
}

export const CropFarmCard: React.FC<CropFarmCardProps> = ({
  recommendation,
  plantingDate,
  farmSize,
}) => {
  const displayCrop = recommendation.crop || 'Selected Crop';
  const displayStage = recommendation.crop_stage || 'Active Growth';
  const displayPlantingDate = plantingDate || 'Not specified';
  const displaySize = farmSize || recommendation.context.farm_size || 'Not specified';

  return (
    <section
      className="dashboard-card crop-farm-card"
      aria-label="Crop and Farm Profile"
      data-testid="crop-farm-card"
    >
      <div className="card-header-row">
        <div className="card-title-group">
          <span className="card-icon" aria-hidden="true">
            🌾
          </span>
          <div>
            <h3 className="card-title">Crop & Farm Profile</h3>
            <p className="card-subtitle">Agronomic setup and growth phase</p>
          </div>
        </div>
      </div>

      <div className="farm-info-grid">
        <div className="info-cell">
          <span className="info-cell-label">Main Crop</span>
          <span className="info-cell-value">{displayCrop}</span>
        </div>

        <div className="info-cell">
          <span className="info-cell-label">Current Growth Stage</span>
          <span className="info-cell-value">{displayStage}</span>
          {recommendation.dap !== null && recommendation.dap !== undefined && (
            <span className="info-cell-sub">Day {recommendation.dap} after planting</span>
          )}
        </div>

        <div className="info-cell">
          <span className="info-cell-label">Planting / Sowing Date</span>
          <span className="info-cell-value">{displayPlantingDate}</span>
        </div>

        <div className="info-cell">
          <span className="info-cell-label">Farm Size</span>
          <span className="info-cell-value">{displaySize}</span>
        </div>
      </div>
    </section>
  );
};
