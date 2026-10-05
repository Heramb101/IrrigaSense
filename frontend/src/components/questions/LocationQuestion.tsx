import React from 'react';
import type { QuestionDefinition } from '../../assessment/assessmentConfig';
import { useAssessment } from '../../context/useAssessment';
import { GoogleMapLocationPicker } from './GoogleMapLocationPicker';

interface LocationQuestionProps {
  definition: QuestionDefinition;
}

export const LocationQuestion: React.FC<LocationQuestionProps> = ({ definition }) => {
  const { state, updateSectionData } = useAssessment();
  const location = state.data.location;

  const handleLocationChange = (loc: {
    latitude: number;
    longitude: number;
    place_name: string;
    location_confirmed: boolean;
  }) => {
    updateSectionData('location', {
      latitude: loc.latitude,
      longitude: loc.longitude,
      place_name: loc.place_name,
      location_name: loc.place_name,
      location_confirmed: false, // Remains false until farmer clicks Confirm Location
    });
  };

  const handleConfirmLocation = (loc: {
    latitude: number;
    longitude: number;
    place_name: string;
  }) => {
    updateSectionData('location', {
      latitude: loc.latitude,
      longitude: loc.longitude,
      place_name: loc.place_name,
      location_name: loc.place_name,
      location_confirmed: true, // Only confirmed on explicit click
    });
  };

  return (
    <div className="question-card location-question-card" data-question-id={definition.id}>
      <div className="question-header">
        <h2>{definition.title}</h2>
        {definition.subtitle && <p className="question-subtitle">{definition.subtitle}</p>}
      </div>

      <div className="question-body">
        <GoogleMapLocationPicker
          selectedLocation={location}
          onLocationChange={handleLocationChange}
          onConfirmLocation={handleConfirmLocation}
        />
      </div>
    </div>
  );
};
