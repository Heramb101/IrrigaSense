import React from 'react';
import type { QuestionDefinition } from '../../assessment/assessmentConfig';
import { useAssessment } from '../../context/useAssessment';
import { OptionCard } from '../ui/OptionCard';

interface CropStageQuestionProps {
  definition: QuestionDefinition;
}

export const CropStageQuestion: React.FC<CropStageQuestionProps> = ({ definition }) => {
  const { state, updateSectionData } = useAssessment();
  const crop = state.data.crop;

  const estimatedStage = crop.calculated_stage || 'Vegetative growth';
  const confirmedStage = crop.farmer_confirmed_stage;
  const stageChoice = crop.stage_choice;

  const isYesSelected = stageChoice === 'yes';
  const isNoSelected = stageChoice === 'no';

  const handleConfirmYes = () => {
    updateSectionData('crop', {
      farmer_confirmed_stage: estimatedStage,
      stage_choice: 'yes',
    });
  };

  const handleSelectNo = () => {
    updateSectionData('crop', {
      stage_choice: 'no',
      farmer_confirmed_stage: confirmedStage && confirmedStage !== estimatedStage ? confirmedStage : '',
    });
  };

  const handleStageSelect = (stageValue: string) => {
    updateSectionData('crop', {
      farmer_confirmed_stage: stageValue,
      stage_choice: 'no',
    });
  };

  const stageOptions = definition.options || [];

  return (
    <div className="question-card" data-question-id={definition.id}>
      <div className="question-header">
        <h2>{definition.title}</h2>
        {definition.subtitle && <p className="question-subtitle">{definition.subtitle}</p>}
      </div>

      <div className="question-body">
        {/* Estimated Stage Banner */}
        <div className="stage-estimate-banner">
          <span className="stage-icon">🌱</span>
          <div className="stage-info">
            <span className="stage-tag">Calculated Stage Estimate</span>
            <h3 className="stage-title">We estimate your crop is currently in the {estimatedStage.toLowerCase()} stage.</h3>
            <p className="stage-desc">
              Based on {crop.planting_date ? `planting date ${crop.planting_date}` : 'typical crop growth curves'}. Does this look accurate?
            </p>
          </div>
        </div>

        {/* Confirmation choices */}
        <div className="options-vertical-list">
          <OptionCard
            value="yes"
            label={`Yes (${estimatedStage})`}
            description="Confirm this estimated growth stage for water requirements"
            icon="✓"
            selected={isYesSelected}
            onClick={handleConfirmYes}
          />
          <OptionCard
            value="no"
            label="No, choose another stage"
            description="Select the actual visual growth stage observed on your farm"
            icon="✏️"
            selected={isNoSelected}
            onClick={handleSelectNo}
          />
        </div>

        {/* Manual Stage Selector List */}
        {isNoSelected && (
          <div className="manual-stage-list">
            <h4 className="stage-selector-header">Select your crop&apos;s current visual stage:</h4>
            <div className="options-vertical-list">
              {stageOptions.map((opt) => (
                <OptionCard
                  key={opt.value}
                  value={opt.value}
                  label={opt.label}
                  selected={confirmedStage === opt.value}
                  onClick={handleStageSelect}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
