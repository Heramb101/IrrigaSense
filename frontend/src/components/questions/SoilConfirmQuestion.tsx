import React from 'react';
import type { QuestionDefinition } from '../../assessment/assessmentConfig';
import { useAssessment } from '../../context/useAssessment';
import { OptionCard } from '../ui/OptionCard';
import { MOCK_SOILGRIDS_DATA } from '../../services/mockData';

interface SoilConfirmQuestionProps {
  definition: QuestionDefinition;
}

export const SoilConfirmQuestion: React.FC<SoilConfirmQuestionProps> = ({ definition }) => {
  const { state, updateSectionData } = useAssessment();
  const soil = state.data.soil;

  const soilgrids = (soil.soilgrids && soil.soilgrids.ph !== null)
    ? soil.soilgrids
    : MOCK_SOILGRIDS_DATA;

  const handleSelectOption = (val: string) => {
    if (val === 'looks_correct') {
      updateSectionData('soil', {
        soilgrids,
        soilgrids_confirmed: true,
        has_soil_report: false,
        soil_choice: 'looks_correct',
      });
    } else if (val === 'have_soil_report') {
      updateSectionData('soil', {
        soilgrids,
        soilgrids_confirmed: false,
        has_soil_report: true,
        soil_choice: 'have_soil_report',
      });
    } else {
      // not_sure
      updateSectionData('soil', {
        soilgrids,
        soilgrids_confirmed: false,
        has_soil_report: false,
        soil_choice: 'not_sure',
      });
    }
  };

  const selectedVal = soil.soil_choice || '';

  return (
    <div className="question-card" data-question-id={definition.id}>
      <div className="question-header">
        <h2>{definition.title}</h2>
        {definition.subtitle && <p className="question-subtitle">{definition.subtitle}</p>}
      </div>

      <div className="question-body">
        {/* SoilGrids Card */}
        <div className="soilgrids-preview-card">
          <div className="soilgrids-badge">
            <span>🔬 Digital Soil Map Estimates (SoilGrids)</span>
          </div>

          <div className="soil-metrics-grid">
            <div className="soil-metric-item">
              <span className="soil-metric-label">Estimated pH</span>
              <span className="soil-metric-value">{soilgrids.ph?.toFixed(1) || '6.6'}</span>
              <span className="soil-metric-sub">Slightly acidic / neutral</span>
            </div>
            <div className="soil-metric-item">
              <span className="soil-metric-label">Clay Content</span>
              <span className="soil-metric-value">{soilgrids.clay?.toFixed(0) || '32'}%</span>
              <span className="soil-metric-sub">Texture fraction</span>
            </div>
            <div className="soil-metric-item">
              <span className="soil-metric-label">Sand Content</span>
              <span className="soil-metric-value">{soilgrids.sand?.toFixed(0) || '40'}%</span>
              <span className="soil-metric-sub">Coarse fraction</span>
            </div>
            <div className="soil-metric-item">
              <span className="soil-metric-label">Organic Carbon</span>
              <span className="soil-metric-value">{soilgrids.organic_carbon?.toFixed(1) || '0.8'}%</span>
              <span className="soil-metric-sub">Organic matter</span>
            </div>
          </div>
        </div>

        <div className="options-vertical-list">
          <OptionCard
            value="looks_correct"
            label="Looks correct"
            description="Use these estimated soil values for water holding and irrigation calculations"
            icon="✓"
            selected={selectedVal === 'looks_correct'}
            onClick={handleSelectOption}
          />
          <OptionCard
            value="have_soil_report"
            label="I have a soil lab test report"
            description="Enter exact N, P, K, and pH values from your Soil Health Card"
            icon="📋"
            selected={selectedVal === 'have_soil_report'}
            onClick={handleSelectOption}
          />
          <OptionCard
            value="not_sure"
            label="I'm not sure"
            description="Continue with standard qualitative soil guidance"
            icon="❓"
            selected={selectedVal === 'not_sure'}
            onClick={handleSelectOption}
          />
        </div>
      </div>
    </div>
  );
};
