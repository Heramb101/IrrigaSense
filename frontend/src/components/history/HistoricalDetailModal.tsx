import React from 'react';
import type { AssessmentRead } from '../../types/assessment';

interface HistoricalDetailModalProps {
  assessment: AssessmentRead;
  onClose: () => void;
  onLoadDraft?: (assessment: AssessmentRead) => void;
}

export const HistoricalDetailModal: React.FC<HistoricalDetailModalProps> = ({
  assessment,
  onClose,
  onLoadDraft,
}) => {
  const data = assessment.data || {};
  const loc = data.location || {};
  const crop = typeof data.crop === 'string' ? data.crop : data.crop?.current_crop_id || 'Not specified';
  const plantingDate = data.planting_date || data.crop?.planting_date || 'Not recorded';
  const farmSize = data.farm?.size_range || data.farm_size || 'Not specified';
  const irrigationMethod = data.irrigation?.method || data.irrigation_method || 'Not specified';
  const waterReliability = data.irrigation?.water_reliability || data.water_availability || 'Not specified';
  const soilDrainage = data.soil?.observed_drainage || 'Not recorded';
  const resolvedPh = data.soil?.resolved?.ph || data.soil?.soilgrids?.ph || data.soil?.farmer_report?.ph;
  const placeName = loc.place_name || loc.location_name || data.place_name || 'Farm coordinates provided';
  const latitude = loc.latitude ?? data.latitude;
  const longitude = loc.longitude ?? data.longitude;

  const formatDate = (dateStr?: string | null) => {
    if (!dateStr) return 'Date unavailable';
    try {
      const d = new Date(dateStr);
      return isNaN(d.getTime()) ? dateStr : d.toLocaleString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="history-modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="history-modal-title">
      <div className="history-detail-card">
        <header className="history-detail-header">
          <div className="history-title-group">
            <span className="history-badge">Assessment #{assessment.id}</span>
            <h2 id="history-modal-title" className="history-heading">
              {crop ? crop.charAt(0).toUpperCase() + crop.slice(1) : 'Farm'} Checkup Snapshot
            </h2>
            <span className="history-timestamp">Recorded on {formatDate(assessment.created_at)}</span>
          </div>
          <button
            type="button"
            className="history-close-btn"
            onClick={onClose}
            aria-label="Close details"
            title="Close details"
          >
            ✕
          </button>
        </header>

        <div className="history-detail-body">
          {/* Section 1: Location */}
          <div className="history-section">
            <h3 className="section-subtitle">📍 Farm Location</h3>
            <div className="history-kv-grid">
              <div className="kv-item">
                <span className="kv-label">Place / Area</span>
                <span className="kv-val">{placeName}</span>
              </div>
              <div className="kv-item">
                <span className="kv-label">Coordinates</span>
                <span className="kv-val">
                  {latitude != null && longitude != null
                    ? `${Number(latitude).toFixed(4)}° N, ${Number(longitude).toFixed(4)}° E`
                    : 'Not specified'}
                </span>
              </div>
            </div>
          </div>

          {/* Section 2: Crop & Agronomy */}
          <div className="history-section">
            <h3 className="section-subtitle">🌾 Crop Profile</h3>
            <div className="history-kv-grid">
              <div className="kv-item">
                <span className="kv-label">Current Crop</span>
                <span className="kv-val highlight-val">{crop}</span>
              </div>
              <div className="kv-item">
                <span className="kv-label">Planting Date</span>
                <span className="kv-val">{plantingDate}</span>
              </div>
              <div className="kv-item">
                <span className="kv-label">Farm Size</span>
                <span className="kv-val">{farmSize}</span>
              </div>
            </div>
          </div>

          {/* Section 3: Water & Soil Context */}
          <div className="history-section">
            <h3 className="section-subtitle">💧 Irrigation & Soil Profile</h3>
            <div className="history-kv-grid">
              <div className="kv-item">
                <span className="kv-label">Irrigation Method</span>
                <span className="kv-val">{irrigationMethod}</span>
              </div>
              <div className="kv-item">
                <span className="kv-label">Water Reliability</span>
                <span className="kv-val">{waterReliability}</span>
              </div>
              <div className="kv-item">
                <span className="kv-label">Observed Drainage</span>
                <span className="kv-val">{soilDrainage}</span>
              </div>
              {resolvedPh != null && (
                <div className="kv-item">
                  <span className="kv-label">Soil pH</span>
                  <span className="kv-val">{resolvedPh}</span>
                </div>
              )}
            </div>
          </div>

          {/* Read-only Advisory Guarantee Notice */}
          <div className="history-notice-box">
            <p className="notice-text">
              🔒 <strong>Read-Only Historical Record:</strong> This assessment was captured using Schema v{assessment.assessment_version}. Live recommendations require current environmental telemetry.
            </p>
          </div>
        </div>

        <footer className="history-detail-footer">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onClose}
          >
            Close
          </button>
          {onLoadDraft && (
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => onLoadDraft(assessment)}
              title="Copy details into a new draft assessment"
            >
              Start New Checkup From This Farm
            </button>
          )}
        </footer>
      </div>
    </div>
  );
};
