import React, { useState, useEffect, useCallback } from 'react';
import { assessmentApi } from '../../services/api';
import type { AssessmentRead } from '../../types/assessment';
import { HistoricalDetailModal } from './HistoricalDetailModal';
import { useAuth } from '../../context/useAuth';

interface AssessmentHistoryViewProps {
  onStartNewAssessment: () => void;
  onReopenAssessment?: (assessment: AssessmentRead) => void;
}

export const AssessmentHistoryView: React.FC<AssessmentHistoryViewProps> = ({
  onStartNewAssessment,
  onReopenAssessment,
}) => {
  const { isAuthenticated } = useAuth();
  const [assessments, setAssessments] = useState<AssessmentRead[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAssessment, setSelectedAssessment] = useState<AssessmentRead | null>(null);

  const fetchHistory = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await assessmentApi.getMyAssessments();
      setAssessments(Array.isArray(data) ? data : []);
    } catch (err: any) {
      const msg = err?.message || 'Failed to load assessment history';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      fetchHistory();
    }
  }, [isAuthenticated, fetchHistory]);

  const formatDate = (dateStr?: string | null) => {
    if (!dateStr) return 'Date unavailable';
    try {
      const d = new Date(dateStr);
      return isNaN(d.getTime()) ? dateStr : d.toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return dateStr;
    }
  };

  const getCropDisplay = (assessment: AssessmentRead) => {
    const data = assessment.data || {};
    const crop = typeof data.crop === 'string' ? data.crop : data.crop?.current_crop_id;
    return crop ? crop.charAt(0).toUpperCase() + crop.slice(1) : 'Standard Crop';
  };

  const getLocationDisplay = (assessment: AssessmentRead) => {
    const data = assessment.data || {};
    const loc = data.location || {};
    if (loc.place_name) return loc.place_name;
    if (loc.location_name) return loc.location_name;
    if (data.place_name) return data.place_name;
    if (loc.latitude != null && loc.longitude != null) {
      return `${Number(loc.latitude).toFixed(3)}°, ${Number(loc.longitude).toFixed(3)}°`;
    }
    return 'Coordinates not recorded';
  };

  const getIrrigationSummary = (assessment: AssessmentRead) => {
    const data = assessment.data || {};
    const method = data.irrigation?.method || data.irrigation_method || 'Standard method';
    const size = data.farm?.size_range || data.farm_size || 'Farm size not recorded';
    return `${size} · ${method}`;
  };

  // Loading State
  if (isLoading) {
    return (
      <div className="history-view-container">
        <header className="history-page-header">
          <div>
            <h2 className="history-page-title">Assessment History</h2>
            <p className="history-page-subtitle">Your previous farm checkups and irrigation records.</p>
          </div>
        </header>

        <div className="history-loading-wrapper" role="status" aria-live="polite">
          <div className="spinner-ring"></div>
          <p className="loading-text">Fetching your farm checkups...</p>
        </div>
      </div>
    );
  }

  // Error State
  if (error) {
    return (
      <div className="history-view-container">
        <header className="history-page-header">
          <div>
            <h2 className="history-page-title">Assessment History</h2>
            <p className="history-page-subtitle">Your previous farm checkups and irrigation records.</p>
          </div>
        </header>

        <div className="history-error-card" role="alert">
          <span className="error-icon">⚠️</span>
          <div className="error-content">
            <h3 className="error-title">Unable to Load Assessment History</h3>
            <p className="error-message">{error}</p>
          </div>
          <div className="error-actions">
            <button
              type="button"
              className="btn btn-primary"
              onClick={fetchHistory}
            >
              ↻ Retry Loading
            </button>
            <button
              type="button"
              className="btn btn-outline"
              onClick={onStartNewAssessment}
            >
              Start New Checkup
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Empty State
  if (assessments.length === 0) {
    return (
      <div className="history-view-container">
        <header className="history-page-header">
          <div>
            <h2 className="history-page-title">Assessment History</h2>
            <p className="history-page-subtitle">Your previous farm checkups and irrigation records.</p>
          </div>
        </header>

        <div className="history-empty-card">
          <div className="empty-icon">🌾</div>
          <h3 className="empty-title">No Previous Assessments Found</h3>
          <p className="empty-subtitle">
            You haven't submitted any farm checkups yet. Answer the 6 farmer questions to receive precision irrigation recommendations based on SoilGrids telemetry and the ANFIS model.
          </p>
          <button
            type="button"
            className="btn btn-primary start-checkup-btn"
            onClick={onStartNewAssessment}
          >
            🌱 Start First Farm Checkup
          </button>
        </div>
      </div>
    );
  }

  // Populated History List
  return (
    <div className="history-view-container">
      <header className="history-page-header">
        <div className="history-header-left">
          <h2 className="history-page-title">Assessment History</h2>
          <span className="history-count-badge">{assessments.length} Records</span>
        </div>

        <div className="history-header-actions">
          <button
            type="button"
            className="btn-history-action refresh-btn"
            onClick={fetchHistory}
            title="Reload assessment history"
          >
            ↻ Refresh
          </button>
          <button
            type="button"
            className="btn-history-action new-checkup-btn"
            onClick={onStartNewAssessment}
            title="Start a new 6-question farm assessment"
          >
            + New Checkup
          </button>
        </div>
      </header>

      <div className="history-cards-grid">
        {assessments.map((item) => (
          <article key={item.id} className="history-card" tabIndex={0}>
            <div className="history-card-top">
              <span className="crop-pill">
                <span className="crop-icon">🌱</span> {getCropDisplay(item)}
              </span>
              <span className="history-date-label">
                {formatDate(item.created_at)}
              </span>
            </div>

            <div className="history-card-body">
              <h4 className="card-location-heading" title={getLocationDisplay(item)}>
                📍 {getLocationDisplay(item)}
              </h4>
              <p className="card-meta-text">
                {getIrrigationSummary(item)}
              </p>
            </div>

            <div className="history-card-footer">
              <span className="version-tag">ID #{item.id} · v{item.assessment_version}</span>
              <button
                type="button"
                className="view-snapshot-btn"
                onClick={() => setSelectedAssessment(item)}
                title={`Inspect snapshot for assessment #${item.id}`}
              >
                View Snapshot 👁️
              </button>
            </div>
          </article>
        ))}
      </div>

      {selectedAssessment && (
        <HistoricalDetailModal
          assessment={selectedAssessment}
          onClose={() => setSelectedAssessment(null)}
          onLoadDraft={onReopenAssessment ? (item) => {
            setSelectedAssessment(null);
            onReopenAssessment(item);
          } : undefined}
        />
      )}
    </div>
  );
};
