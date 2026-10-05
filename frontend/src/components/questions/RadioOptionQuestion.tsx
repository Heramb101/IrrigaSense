import React from 'react';
import type { QuestionDefinition } from '../../assessment/assessmentConfig';
import { useAssessment } from '../../context/useAssessment';
import { OptionCard } from '../ui/OptionCard';
import type { AssessmentData } from '../../types/assessment';

interface RadioOptionQuestionProps {
  definition: QuestionDefinition;
}

export const RadioOptionQuestion: React.FC<RadioOptionQuestionProps> = ({ definition }) => {
  const { state, updateSectionData } = useAssessment();

  // Extract current value based on dataPath (supports both top-level and dot-notated paths)
  const getSelectedValue = (path: string, obj: AssessmentData): string => {
    if (!path) return '';
    if (!path.includes('.')) {
      const val = (obj as any)[path];
      return typeof val === 'string' ? val : '';
    }

    const parts = path.split('.');
    let current: unknown = obj;
    for (const part of parts) {
      if (current && typeof current === 'object' && part in current) {
        current = (current as Record<string, unknown>)[part];
      } else {
        return '';
      }
    }
    return typeof current === 'string' ? current : '';
  };

  const currentValue = getSelectedValue(definition.dataPath, state.data);
  const options = definition.options || [];

  const handleSelect = (val: string) => {
    if (definition.dataPath.includes('.')) {
      const [section, field] = definition.dataPath.split('.');
      updateSectionData(section, { [field]: val });
    } else {
      updateSectionData(definition.dataPath, val);
    }
  };

  return (
    <div className="question-card" data-question-id={definition.id}>
      <div className="question-header">
        <h2>{definition.title}</h2>
        {definition.subtitle && <p className="question-subtitle">{definition.subtitle}</p>}
      </div>

      <div className="question-body">
        <div className="options-vertical-list">
          {options.map((opt) => (
            <OptionCard
              key={opt.value}
              value={opt.value}
              label={opt.label}
              description={opt.description}
              icon={opt.icon}
              selected={currentValue === opt.value}
              onClick={handleSelect}
            />
          ))}
        </div>
      </div>
    </div>
  );
};
