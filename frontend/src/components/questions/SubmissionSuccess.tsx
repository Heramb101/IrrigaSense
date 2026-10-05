import React, { useState } from 'react';
import { useAssessment } from '../../context/useAssessment';

export const SubmissionSuccess: React.FC = () => {
  const { finalSubmission, resetAssessment } = useAssessment();
  const [showJsonPayload, setShowJsonPayload] = useState<boolean>(false);

  const data = finalSubmission?.payload.data;

  return (
    <div className="submission-success-card">
      <div className="success-icon-badge">🎉</div>
      <h2 className="success-heading">Farm Checkup Assessment Completed!</h2>
      <p className="success-subtext">
        Your 6-point farm setup and environmental baseline have been collected successfully.
      </p>

      <div className="success-highlights-grid">
        <div className="highlight-item">
          <span className="hl-label">Farm Location</span>
          <span className="hl-val">
            {data?.location.place_name || data?.location.location_name || 'Selected Farmland'}
          </span>
        </div>
        <div className="highlight-item">
          <span className="hl-label">Main Crop</span>
          <span className="hl-val">{data?.crop || 'Not specified'}</span>
        </div>
        <div className="highlight-item">
          <span className="hl-label">Planting Date</span>
          <span className="hl-val">{data?.planting_date || 'Not specified'}</span>
        </div>
        <div className="highlight-item">
          <span className="hl-label">Farm Size</span>
          <span className="hl-val">{data?.farm_size || 'Not specified'}</span>
        </div>
        <div className="highlight-item">
          <span className="hl-label">Irrigation Method</span>
          <span className="hl-val">{data?.irrigation_method || 'Not specified'}</span>
        </div>
        <div className="highlight-item">
          <span className="hl-label">Water Availability</span>
          <span className="hl-val">{data?.water_availability || 'Not specified'}</span>
        </div>
      </div>

      <div className="payload-inspect-box">
        <button
          type="button"
          className="toggle-link-btn"
          onClick={() => setShowJsonPayload(!showJsonPayload)}
        >
          {showJsonPayload
            ? '− Hide Structured JSON Payload (Dev Mode)'
            : '+ View Structured Assessment JSON Payload (POST /api/assessments)'}
        </button>

        {showJsonPayload && (
          <pre className="json-payload-pre">
            {JSON.stringify(finalSubmission?.payload, null, 2)}
          </pre>
        )}
      </div>

      <div className="success-actions-row">
        <button
          type="button"
          className="btn btn-secondary"
          onClick={resetAssessment}
        >
          ↺ Start a New Assessment
        </button>
      </div>
    </div>
  );
};
