import React from 'react';
import type { QuestionDefinition, QuestionId } from '../../assessment/assessmentConfig';
import { useAssessment } from '../../context/useAssessment';

interface ReviewSummaryQuestionProps {
  definition: QuestionDefinition;
}

export const ReviewSummaryQuestion: React.FC<ReviewSummaryQuestionProps> = ({ definition }) => {
  const { state, goToQuestion, submitAssessment } = useAssessment();
  const data = state.data;

  const handleEditSection = (targetQuestionId: QuestionId) => {
    goToQuestion(targetQuestionId);
  };

  const hasLocation = data.location && data.location.latitude !== 0 && data.location.longitude !== 0;

  return (
    <div className="question-card review-screen-card" data-question-id={definition.id}>
      <div className="question-header">
        <h2>{definition.title}</h2>
        {definition.subtitle && <p className="question-subtitle">{definition.subtitle}</p>}
      </div>

      <div className="review-sections-list">
        {/* 1. Farm Location */}
        <div className="review-group-card">
          <div className="review-group-header">
            <div className="review-group-title-row">
              <span className="review-group-icon">📍</span>
              <h3>1. Farm Location</h3>
            </div>
            <button
              type="button"
              className="edit-section-btn"
              onClick={() => handleEditSection('Q1')}
            >
              ✏️ Edit
            </button>
          </div>
          <div className="review-key-values">
            <div className="review-row">
              <span className="review-key">Location:</span>
              <span className="review-val">
                {data.location.place_name || data.location.location_name || 'Selected Farmland'}
              </span>
            </div>
            <div className="review-row">
              <span className="review-key">Coordinates:</span>
              <span className="review-val">
                {hasLocation
                  ? `${data.location.latitude.toFixed(5)}° N, ${data.location.longitude.toFixed(5)}° E`
                  : 'Not specified'}
              </span>
            </div>
          </div>
        </div>

        {/* 2. Current Crop */}
        <div className="review-group-card">
          <div className="review-group-header">
            <div className="review-group-title-row">
              <span className="review-group-icon">🌾</span>
              <h3>2. Current Crop</h3>
            </div>
            <button
              type="button"
              className="edit-section-btn"
              onClick={() => handleEditSection('Q2')}
            >
              ✏️ Edit
            </button>
          </div>
          <div className="review-key-values">
            <div className="review-row">
              <span className="review-key">Main Crop:</span>
              <span className="review-val">{data.crop || 'Not selected'}</span>
            </div>
          </div>
        </div>

        {/* 3. Planting Date */}
        <div className="review-group-card">
          <div className="review-group-header">
            <div className="review-group-title-row">
              <span className="review-group-icon">📅</span>
              <h3>3. Planting Date</h3>
            </div>
            <button
              type="button"
              className="edit-section-btn"
              onClick={() => handleEditSection('Q3')}
            >
              ✏️ Edit
            </button>
          </div>
          <div className="review-key-values">
            <div className="review-row">
              <span className="review-key">Sowing / Transplant Date:</span>
              <span className="review-val">{data.planting_date || 'Not specified'}</span>
            </div>
          </div>
        </div>

        {/* 4. Farm Size */}
        <div className="review-group-card">
          <div className="review-group-header">
            <div className="review-group-title-row">
              <span className="review-group-icon">🚜</span>
              <h3>4. Farm Size</h3>
            </div>
            <button
              type="button"
              className="edit-section-btn"
              onClick={() => handleEditSection('Q4')}
            >
              ✏️ Edit
            </button>
          </div>
          <div className="review-key-values">
            <div className="review-row">
              <span className="review-key">Acreage:</span>
              <span className="review-val">{data.farm_size || 'Not specified'}</span>
            </div>
          </div>
        </div>

        {/* 5. Irrigation Method */}
        <div className="review-group-card">
          <div className="review-group-header">
            <div className="review-group-title-row">
              <span className="review-group-icon">💧</span>
              <h3>5. Irrigation Method</h3>
            </div>
            <button
              type="button"
              className="edit-section-btn"
              onClick={() => handleEditSection('Q5')}
            >
              ✏️ Edit
            </button>
          </div>
          <div className="review-key-values">
            <div className="review-row">
              <span className="review-key">Method:</span>
              <span className="review-val">{data.irrigation_method || 'Not specified'}</span>
            </div>
          </div>
        </div>

        {/* 6. Water Availability */}
        <div className="review-group-card">
          <div className="review-group-header">
            <div className="review-group-title-row">
              <span className="review-group-icon">🌊</span>
              <h3>6. Water Availability</h3>
            </div>
            <button
              type="button"
              className="edit-section-btn"
              onClick={() => handleEditSection('Q6')}
            >
              ✏️ Edit
            </button>
          </div>
          <div className="review-key-values">
            <div className="review-row">
              <span className="review-key">Water Security:</span>
              <span className="review-val">{data.water_availability || 'Not specified'}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="final-submit-box">
        <button
          type="button"
          className="btn btn-primary submit-assessment-btn"
          onClick={submitAssessment}
        >
          ✓ Confirm & Submit Assessment
        </button>
      </div>
    </div>
  );
};
