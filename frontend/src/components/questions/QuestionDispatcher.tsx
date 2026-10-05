import React from 'react';
import { useAssessment } from '../../context/useAssessment';
import { LocationQuestion } from './LocationQuestion';
import { CropSelectQuestion } from './CropSelectQuestion';
import { PlantingDateQuestion } from './PlantingDateQuestion';
import { RadioOptionQuestion } from './RadioOptionQuestion';
import { ReviewSummaryQuestion } from './ReviewSummaryQuestion';
import { Dashboard } from '../../dashboard/Dashboard';


export const QuestionDispatcher: React.FC = () => {
  const { currentQuestionDefinition, state, resetAssessment } = useAssessment();

  if (state.isCompleted) {
    return <Dashboard onStartNewAssessment={resetAssessment} />;
  }


  if (!currentQuestionDefinition) {
    return (
      <div className="empty-state-card">
        <h2>Assessment Step: {state.currentQuestionId}</h2>
        <p>Step definition not found.</p>
      </div>
    );
  }

  switch (currentQuestionDefinition.id) {
    case 'Q1':
      return <LocationQuestion definition={currentQuestionDefinition} />;
    case 'Q2':
      return <CropSelectQuestion definition={currentQuestionDefinition} />;
    case 'Q3':
      return <PlantingDateQuestion definition={currentQuestionDefinition} />;
    case 'Q4':
    case 'Q5':
    case 'Q6':
      return <RadioOptionQuestion definition={currentQuestionDefinition} />;
    case 'REVIEW':
      return <ReviewSummaryQuestion definition={currentQuestionDefinition} />;
    default:
      return (
        <div className="question-card">
          <h2>{currentQuestionDefinition.title}</h2>
          <p>{currentQuestionDefinition.subtitle}</p>
        </div>
      );
  }
};
