import React from 'react';
import type { QuestionDefinition } from '../../assessment/assessmentConfig';
import { useAssessment } from '../../context/useAssessment';

interface PlantingDateQuestionProps {
  definition: QuestionDefinition;
}

export const PlantingDateQuestion: React.FC<PlantingDateQuestionProps> = ({ definition }) => {
  const { state, updateSectionData } = useAssessment();
  const selectedDate = state.data.planting_date || '';

  const handleDateChange = (dateStr: string) => {
    updateSectionData('planting_date', dateStr);
  };

  const setPresetDate = (daysAgo: number) => {
    const d = new Date();
    d.setDate(d.getDate() - daysAgo);
    const dateStr = d.toISOString().split('T')[0];
    updateSectionData('planting_date', dateStr);
  };

  // Get today's date formatted as YYYY-MM-DD for calendar max constraint
  const todayStr = new Date().toISOString().split('T')[0];

  return (
    <div className="question-card" data-question-id={definition.id}>
      <div className="question-header">
        <h2>{definition.title}</h2>
        {definition.subtitle && <p className="question-subtitle">{definition.subtitle}</p>}
      </div>

      <div className="question-body">
        {/* Quick Date Presets */}
        <div className="date-presets-block">
          <span className="presets-header-label">Quick Presets:</span>
          <div className="chips-row">
            <button
              type="button"
              className="chip-btn"
              onClick={() => setPresetDate(0)}
            >
              Today
            </button>
            <button
              type="button"
              className="chip-btn"
              onClick={() => setPresetDate(14)}
            >
              2 weeks ago (~14 days)
            </button>
            <button
              type="button"
              className="chip-btn"
              onClick={() => setPresetDate(30)}
            >
              1 month ago (~30 days)
            </button>
            <button
              type="button"
              className="chip-btn"
              onClick={() => setPresetDate(60)}
            >
              2 months ago (~60 days)
            </button>
            <button
              type="button"
              className="chip-btn"
              onClick={() => setPresetDate(90)}
            >
              3 months ago (~90 days)
            </button>
          </div>
        </div>

        {/* Date Input Box */}
        <div className="custom-date-picker-box">
          <label htmlFor="planting-date-input" className="date-picker-label">
            Selected Sowing / Transplanting Date:
          </label>
          <input
            id="planting-date-input"
            type="date"
            max={todayStr}
            className="date-input-field"
            value={selectedDate}
            onChange={(e) => handleDateChange(e.target.value)}
          />
        </div>
      </div>
    </div>
  );
};
