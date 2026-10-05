import React from 'react';
import type { QuestionDefinition } from '../../assessment/assessmentConfig';
import { useAssessment } from '../../context/useAssessment';
import { OptionCard } from '../ui/OptionCard';
import { MapPlaceholder } from './MapPlaceholder';

interface LocationConfirmQuestionProps {
  definition: QuestionDefinition;
}

export const LocationConfirmQuestion: React.FC<LocationConfirmQuestionProps> = ({ definition }) => {
  const { state, updateSectionData, goToQuestion } = useAssessment();
  const location = state.data.location;

  const handleConfirmChoice = (value: string) => {
    if (value === 'yes') {
      updateSectionData('location', {
        location_confirmed: true,
      });
    } else {
      // Return to Q1 to pick another location
      updateSectionData('location', {
        location_confirmed: false,
      });
      goToQuestion('Q1');
    }
  };

  const isConfirmed = location.location_confirmed === true;

  return (
    <div className="question-card" data-question-id={definition.id}>
      <div className="question-header">
        <h2>{definition.title}</h2>
        {definition.subtitle && <p className="question-subtitle">{definition.subtitle}</p>}
      </div>

      <div className="question-body">
        <div className="location-summary-card">
          <div className="location-summary-header">
            <span className="location-icon">📍</span>
            <div>
              <h3 className="location-name">{location.location_name || 'Selected Farmland'}</h3>
              <p className="location-coords">
                Coordinates: {location.latitude.toFixed(4)}° N, {location.longitude.toFixed(4)}° E
              </p>
            </div>
          </div>
          
          <MapPlaceholder
            selectedLocation={location}
            onSelectLocation={() => {}}
            interactive={false}
          />
        </div>

        <div className="options-vertical-list">
          <OptionCard
            value="yes"
            label="YES (This is my farm)"
            description="Confirm this location and proceed to environmental checkup"
            icon="✓"
            selected={isConfirmed}
            onClick={handleConfirmChoice}
          />
          <OptionCard
            value="no"
            label="CHANGE LOCATION"
            description="Return to the map to choose a different farm location"
            icon="↺"
            selected={false}
            onClick={handleConfirmChoice}
          />
        </div>
      </div>
    </div>
  );
};
