import React from 'react';
import type { QuestionDefinition } from '../../assessment/assessmentConfig';
import { useAssessment } from '../../context/useAssessment';
import { OptionCard } from '../ui/OptionCard';

interface IrrigationCompoundQuestionProps {
  definition: QuestionDefinition;
}

const FREQUENCY_OPTIONS = [
  { value: 'Daily', label: 'Daily', description: 'Irrigate every day', icon: '🗓️' },
  { value: 'Every 2–3 days', label: 'Every 2–3 days', description: 'Regular interval watering', icon: '⏱️' },
  { value: 'About once a week', label: 'About once a week', description: 'Weekly watering cycle', icon: '📅' },
  { value: 'Only when the soil looks dry', label: 'Only when the soil looks dry', description: 'Visual soil dryness check', icon: '👀' },
  { value: 'Based on weather', label: 'Based on weather & heat', description: 'Skip on cloudy/rainy days, increase in heat', icon: '⛅' },
  { value: 'Other', label: 'Other schedule', description: 'Custom rotational schedule', icon: '⚙️' },
];

const LAST_IRRIGATION_OPTIONS = [
  { value: 'Today', label: 'Today', description: 'Watered within the last 12–24 hours', icon: '💧' },
  { value: 'Yesterday', label: 'Yesterday', description: 'Watered 1 day ago', icon: '🌱' },
  { value: '2–3 days ago', label: '2–3 days ago', description: 'Recent watering', icon: '⏳' },
  { value: '4–7 days ago', label: '4–7 days ago', description: 'About a week ago', icon: '🌾' },
  { value: 'More than a week ago', label: 'More than a week ago', description: 'Dry interval > 7 days', icon: '☀️' },
  { value: "I don't remember", label: "I don't remember", description: 'Approximate / uncertain', icon: '❓' },
  { value: 'Not applicable', label: 'Not applicable', description: 'New field or not recently irrigated', icon: '⚪' },
];

export const IrrigationCompoundQuestion: React.FC<IrrigationCompoundQuestionProps> = ({ definition }) => {
  const { state, updateSectionData } = useAssessment();
  const irrigation = state.data.irrigation;

  const handleFrequencySelect = (val: string) => {
    updateSectionData('irrigation', {
      current_frequency: val,
    });
  };

  const handleLastIrrigationSelect = (val: string) => {
    updateSectionData('irrigation', {
      last_irrigation: val,
    });
  };

  return (
    <div className="question-card" data-question-id={definition.id}>
      <div className="question-header">
        <h2>{definition.title}</h2>
        {definition.subtitle && <p className="question-subtitle">{definition.subtitle}</p>}
      </div>

      <div className="question-body">
        {/* Section 1: Frequency */}
        <div className="compound-section-block">
          <h3 className="compound-section-title">1. How often do you currently irrigate?</h3>
          <div className="options-vertical-list">
            {FREQUENCY_OPTIONS.map((opt) => (
              <OptionCard
                key={opt.value}
                value={opt.value}
                label={opt.label}
                description={opt.description}
                icon={opt.icon}
                selected={irrigation.current_frequency === opt.value}
                onClick={handleFrequencySelect}
              />
            ))}
          </div>
        </div>

        {/* Section 2: Last Irrigation */}
        <div className="compound-section-block" style={{ marginTop: '28px' }}>
          <h3 className="compound-section-title">2. When was the last time you irrigated?</h3>
          <div className="options-vertical-list">
            {LAST_IRRIGATION_OPTIONS.map((opt) => (
              <OptionCard
                key={opt.value}
                value={opt.value}
                label={opt.label}
                description={opt.description}
                icon={opt.icon}
                selected={irrigation.last_irrigation === opt.value}
                onClick={handleLastIrrigationSelect}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
