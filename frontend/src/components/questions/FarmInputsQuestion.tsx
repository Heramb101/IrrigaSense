import React from 'react';
import type { QuestionDefinition } from '../../assessment/assessmentConfig';
import { useAssessment } from '../../context/useAssessment';
import { OptionCard } from '../ui/OptionCard';

interface FarmInputsQuestionProps {
  definition: QuestionDefinition;
}

const FERTILIZER_OPTIONS = [
  { value: 'Organic manure', label: 'Organic manure', description: 'FYM, Vermicompost, Cow dung manure', icon: '🍂' },
  { value: 'Urea', label: 'Urea', description: 'Quick-release nitrogen fertilizer (46% N)', icon: '⚪' },
  { value: 'DAP', label: 'DAP', description: 'Di-Ammonium Phosphate (Phosphorus & Nitrogen)', icon: '🪨' },
  { value: 'NPK fertilizer', label: 'NPK fertilizer', description: 'Balanced complex fertilizers (10:26:26, 19:19:19, etc.)', icon: '🧪' },
  { value: 'Other', label: 'Other', description: 'Other fertilizers or micronutrient sprays', icon: '➕' },
  { value: 'None', label: 'None', description: 'No fertilizers applied', icon: '❌' },
];

const PEST_OPTIONS = [
  { value: 'Insecticides', label: 'Insecticides', description: 'Chemical or organic insect pest controls', icon: '🐛' },
  { value: 'Fungicides', label: 'Fungicides', description: 'Fungal root rot, blight, and mildew controls', icon: '🍄' },
  { value: 'Herbicides', label: 'Herbicides', description: 'Pre-emergence and post-emergence weed control', icon: '🌱' },
  { value: 'Other', label: 'Other', description: 'Other pest, disease, or biological controls', icon: '➕' },
  { value: 'None', label: 'None', description: 'No pest control chemicals applied', icon: '❌' },
];

export const FarmInputsQuestion: React.FC<FarmInputsQuestionProps> = ({ definition }) => {
  const { state, updateSectionData } = useAssessment();
  const inputs = state.data.farm_inputs;
  const [otherFertilizer, setOtherFertilizer] = React.useState<string>('');
  const [otherPest, setOtherPest] = React.useState<string>('');

  const selectedFertilizers = inputs.fertilizers || [];
  const selectedPest = inputs.pest_control || [];

  const handleToggleFertilizer = (val: string) => {
    let next: string[];
    if (val === 'None') {
      next = selectedFertilizers.includes('None') ? [] : ['None'];
    } else {
      const filtered = selectedFertilizers.filter((i) => i !== 'None');
      if (filtered.includes(val)) {
        next = filtered.filter((i) => i !== val);
      } else {
        next = [...filtered, val];
      }
    }
    updateSectionData('farm_inputs', {
      fertilizers: next,
    });
  };

  const handleOtherFertilizerBlur = () => {
    if (!otherFertilizer.trim()) return;
    const custom = `Other: ${otherFertilizer.trim()}`;
    const filtered = selectedFertilizers.filter((i) => !i.startsWith('Other'));
    updateSectionData('farm_inputs', {
      fertilizers: [...filtered, custom],
    });
  };

  const handleTogglePest = (val: string) => {
    let next: string[];
    if (val === 'None') {
      next = selectedPest.includes('None') ? [] : ['None'];
    } else {
      const filtered = selectedPest.filter((i) => i !== 'None');
      if (filtered.includes(val)) {
        next = filtered.filter((i) => i !== val);
      } else {
        next = [...filtered, val];
      }
    }
    updateSectionData('farm_inputs', {
      pest_control: next,
    });
  };

  const handleOtherPestBlur = () => {
    if (!otherPest.trim()) return;
    const custom = `Other: ${otherPest.trim()}`;
    const filtered = selectedPest.filter((i) => !i.startsWith('Other'));
    updateSectionData('farm_inputs', {
      pest_control: [...filtered, custom],
    });
  };

  const isOtherFertilizerSelected = selectedFertilizers.some((i) => i === 'Other' || i.startsWith('Other:'));
  const isOtherPestSelected = selectedPest.some((i) => i === 'Other' || i.startsWith('Other:'));

  return (
    <div className="question-card" data-question-id={definition.id}>
      <div className="question-header">
        <h2>{definition.title}</h2>
        {definition.subtitle && <p className="question-subtitle">{definition.subtitle}</p>}
      </div>

      <div className="question-body">
        {/* Section A: Fertilizers */}
        <div className="compound-section-block">
          <div className="section-subtitle-bar">
            <span className="section-sub-icon">🌾</span>
            <h3 className="compound-section-title">FERTILIZERS</h3>
          </div>
          <div className="options-vertical-list">
            {FERTILIZER_OPTIONS.map((opt) => (
              <OptionCard
                key={opt.value}
                value={opt.value}
                label={opt.label}
                description={opt.description}
                icon={opt.icon}
                selected={
                  opt.value === 'Other'
                    ? isOtherFertilizerSelected
                    : selectedFertilizers.includes(opt.value)
                }
                isMulti={true}
                onClick={handleToggleFertilizer}
              />
            ))}
          </div>

          {isOtherFertilizerSelected && (
            <div className="other-input-container" style={{ marginTop: '12px' }}>
              <input
                type="text"
                className="text-input-field"
                placeholder="Specify other fertilizer details..."
                value={otherFertilizer}
                onChange={(e) => setOtherFertilizer(e.target.value)}
                onBlur={handleOtherFertilizerBlur}
              />
            </div>
          )}
        </div>

        {/* Section B: Pest Control */}
        <div className="compound-section-block" style={{ marginTop: '32px' }}>
          <div className="section-subtitle-bar">
            <span className="section-sub-icon">🛡️</span>
            <h3 className="compound-section-title">PEST CONTROL</h3>
          </div>
          <div className="options-vertical-list">
            {PEST_OPTIONS.map((opt) => (
              <OptionCard
                key={opt.value}
                value={opt.value}
                label={opt.label}
                description={opt.description}
                icon={opt.icon}
                selected={
                  opt.value === 'Other'
                    ? isOtherPestSelected
                    : selectedPest.includes(opt.value)
                }
                isMulti={true}
                onClick={handleTogglePest}
              />
            ))}
          </div>

          {isOtherPestSelected && (
            <div className="other-input-container" style={{ marginTop: '12px' }}>
              <input
                type="text"
                className="text-input-field"
                placeholder="Specify other pest control details..."
                value={otherPest}
                onChange={(e) => setOtherPest(e.target.value)}
                onBlur={handleOtherPestBlur}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
