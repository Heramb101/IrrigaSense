import React from 'react';
import type { QuestionDefinition } from '../../assessment/assessmentConfig';
import { useAssessment } from '../../context/useAssessment';

interface SoilReportQuestionProps {
  definition: QuestionDefinition;
}

export const SoilReportQuestion: React.FC<SoilReportQuestionProps> = ({ definition }) => {
  const { state, updateSectionData } = useAssessment();
  const report = state.data.soil.farmer_report || {
    n: null,
    p: null,
    k: null,
    ph: null,
    units: { n: 'kg/ha', p: 'kg/ha', k: 'kg/ha' },
  };

  const units = report.units || { n: 'kg/ha', p: 'kg/ha', k: 'kg/ha' };

  const handleValueChange = (field: 'n' | 'p' | 'k' | 'ph', valStr: string) => {
    const val = valStr === '' ? null : parseFloat(valStr);
    updateSectionData('soil', {
      farmer_report: {
        ...report,
        [field]: isNaN(val as number) ? null : val,
        units,
      },
    });
  };

  const handleUnitChange = (nutrient: 'n' | 'p' | 'k', unitVal: string) => {
    updateSectionData('soil', {
      farmer_report: {
        ...report,
        units: {
          ...units,
          [nutrient]: unitVal,
        },
      },
    });
  };

  return (
    <div className="question-card" data-question-id={definition.id}>
      <div className="question-header">
        <h2>{definition.title}</h2>
        {definition.subtitle && <p className="question-subtitle">{definition.subtitle}</p>}
      </div>

      <div className="question-body">
        <div className="soil-report-grid">
          {/* Nitrogen */}
          <div className="soil-nutrient-card">
            <div className="nutrient-label-row">
              <label htmlFor="soil-n" className="nutrient-name">
                Nitrogen (N)
              </label>
              <span className="nutrient-hint">Available Nitrogen</span>
            </div>
            <div className="input-with-unit-group">
              <input
                id="soil-n"
                type="number"
                step="0.1"
                min="0"
                className="nutrient-input-field"
                placeholder="e.g. 240"
                value={report.n ?? ''}
                onChange={(e) => handleValueChange('n', e.target.value)}
              />
              <select
                className="unit-select-field"
                value={units.n || 'kg/ha'}
                onChange={(e) => handleUnitChange('n', e.target.value)}
              >
                <option value="kg/ha">kg/ha</option>
                <option value="ppm">ppm</option>
                <option value="mg/kg">mg/kg</option>
                <option value="%">%</option>
              </select>
            </div>
            <div className="quick-unknown-row">
              <button
                type="button"
                className={`mini-chip-btn ${report.n === null ? 'active' : ''}`}
                onClick={() => handleValueChange('n', '')}
              >
                Don't know / Not available
              </button>
            </div>
          </div>

          {/* Phosphorus */}
          <div className="soil-nutrient-card">
            <div className="nutrient-label-row">
              <label htmlFor="soil-p" className="nutrient-name">
                Phosphorus (P)
              </label>
              <span className="nutrient-hint">Available P₂O₅</span>
            </div>
            <div className="input-with-unit-group">
              <input
                id="soil-p"
                type="number"
                step="0.1"
                min="0"
                className="nutrient-input-field"
                placeholder="e.g. 18.5"
                value={report.p ?? ''}
                onChange={(e) => handleValueChange('p', e.target.value)}
              />
              <select
                className="unit-select-field"
                value={units.p || 'kg/ha'}
                onChange={(e) => handleUnitChange('p', e.target.value)}
              >
                <option value="kg/ha">kg/ha</option>
                <option value="ppm">ppm</option>
                <option value="mg/kg">mg/kg</option>
                <option value="%">%</option>
              </select>
            </div>
            <div className="quick-unknown-row">
              <button
                type="button"
                className={`mini-chip-btn ${report.p === null ? 'active' : ''}`}
                onClick={() => handleValueChange('p', '')}
              >
                Don't know / Not available
              </button>
            </div>
          </div>

          {/* Potassium */}
          <div className="soil-nutrient-card">
            <div className="nutrient-label-row">
              <label htmlFor="soil-k" className="nutrient-name">
                Potassium (K)
              </label>
              <span className="nutrient-hint">Available K₂O</span>
            </div>
            <div className="input-with-unit-group">
              <input
                id="soil-k"
                type="number"
                step="0.1"
                min="0"
                className="nutrient-input-field"
                placeholder="e.g. 310"
                value={report.k ?? ''}
                onChange={(e) => handleValueChange('k', e.target.value)}
              />
              <select
                className="unit-select-field"
                value={units.k || 'kg/ha'}
                onChange={(e) => handleUnitChange('k', e.target.value)}
              >
                <option value="kg/ha">kg/ha</option>
                <option value="ppm">ppm</option>
                <option value="mg/kg">mg/kg</option>
                <option value="%">%</option>
              </select>
            </div>
            <div className="quick-unknown-row">
              <button
                type="button"
                className={`mini-chip-btn ${report.k === null ? 'active' : ''}`}
                onClick={() => handleValueChange('k', '')}
              >
                Don't know / Not available
              </button>
            </div>
          </div>

          {/* Soil pH */}
          <div className="soil-nutrient-card">
            <div className="nutrient-label-row">
              <label htmlFor="soil-ph" className="nutrient-name">
                Soil pH
              </label>
              <span className="nutrient-hint">Acidity / Alkalinity (0–14)</span>
            </div>
            <div className="input-with-unit-group">
              <input
                id="soil-ph"
                type="number"
                step="0.1"
                min="0"
                max="14"
                className="nutrient-input-field"
                placeholder="e.g. 6.8"
                value={report.ph ?? ''}
                onChange={(e) => handleValueChange('ph', e.target.value)}
              />
              <span className="unit-static-badge">pH scale</span>
            </div>
            <div className="quick-unknown-row">
              <button
                type="button"
                className={`mini-chip-btn ${report.ph === null ? 'active' : ''}`}
                onClick={() => handleValueChange('ph', '')}
              >
                Don't know / Not available
              </button>
            </div>
          </div>
        </div>

        <p className="form-help-footer">
          ℹ️ Enter values present on your card. If unknown or not available, leave blank or tap &quot;Don&apos;t know&quot;.
        </p>
      </div>
    </div>
  );
};
