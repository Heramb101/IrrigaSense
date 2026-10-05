import React, { useState } from 'react';
import type { QuestionDefinition } from '../../assessment/assessmentConfig';
import { useAssessment } from '../../context/useAssessment';
import { OptionCard } from '../ui/OptionCard';
import type { AssessmentData } from '../../types/assessment';

interface MultiSelectQuestionProps {
  definition: QuestionDefinition;
}

export const MultiSelectQuestion: React.FC<MultiSelectQuestionProps> = ({ definition }) => {
  const { state, updateSectionData } = useAssessment();
  const [otherText, setOtherText] = useState<string>('');

  const getArrayValue = (path: string, obj: AssessmentData): string[] => {
    const parts = path.split('.');
    let current: unknown = obj;
    for (const part of parts) {
      if (current && typeof current === 'object' && part in current) {
        current = (current as Record<string, unknown>)[part];
      } else {
        return [];
      }
    }
    return Array.isArray(current) ? (current as string[]) : [];
  };

  const selectedItems = getArrayValue(definition.dataPath, state.data);
  const options = definition.options || [];

  const handleToggle = (val: string) => {
    const parts = definition.dataPath.split('.');
    const section = parts[0] as keyof AssessmentData;
    const field = parts[1];

    let newItems: string[];

    // Mutual exclusivity for "None", "Don't know", "This is new farmland"
    const exclusiveOptions = ['None', "Don't know", 'This is new farmland'];

    if (exclusiveOptions.includes(val)) {
      if (selectedItems.includes(val)) {
        newItems = selectedItems.filter((i) => i !== val);
      } else {
        newItems = [val];
      }
    } else {
      // Regular option: remove any mutually exclusive items
      const cleaned = selectedItems.filter((i) => !exclusiveOptions.includes(i));
      if (cleaned.includes(val)) {
        newItems = cleaned.filter((i) => i !== val);
      } else {
        newItems = [...cleaned, val];
      }
    }

    updateSectionData(section, {
      [field]: newItems,
    } as unknown as Partial<AssessmentData[typeof section]>);
  };

  const handleOtherInputBlur = () => {
    if (!otherText.trim()) return;
    const parts = definition.dataPath.split('.');
    const section = parts[0] as keyof AssessmentData;
    const field = parts[1];

    const customEntry = `Other: ${otherText.trim()}`;
    const filtered = selectedItems.filter((i) => !i.startsWith('Other:'));
    const newItems = [...filtered, customEntry];

    updateSectionData(section, {
      [field]: newItems,
    } as unknown as Partial<AssessmentData[typeof section]>);
  };

  const isOtherActive =
    selectedItems.some((i) => i === 'Other' || i.startsWith('Other:')) ||
    (definition.allowOther && otherText.length > 0);

  return (
    <div className="question-card" data-question-id={definition.id}>
      <div className="question-header">
        <h2>{definition.title}</h2>
        {definition.subtitle && <p className="question-subtitle">{definition.subtitle}</p>}
      </div>

      <div className="question-body">
        <div className="options-vertical-list">
          {options.map((opt) => {
            const isSelected = selectedItems.includes(opt.value);
            return (
              <OptionCard
                key={opt.value}
                value={opt.value}
                label={opt.label}
                description={opt.description}
                icon={opt.icon}
                selected={isSelected}
                isMulti={true}
                onClick={handleToggle}
              />
            );
          })}
        </div>

        {definition.allowOther && (
          <div className="other-custom-section">
            <OptionCard
              value="Other"
              label="Other (Type your own)"
              description="Specify if your option is not in the list above"
              icon="➕"
              selected={!!isOtherActive}
              isMulti={true}
              onClick={() => handleToggle('Other')}
            />

            {isOtherActive && (
              <div className="other-input-container">
                <input
                  type="text"
                  className="text-input-field"
                  placeholder="Specify other details here..."
                  value={otherText}
                  onChange={(e) => setOtherText(e.target.value)}
                  onBlur={handleOtherInputBlur}
                />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
