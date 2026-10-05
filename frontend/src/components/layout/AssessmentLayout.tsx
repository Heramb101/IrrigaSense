import React from 'react';
import { ProgressBar } from './ProgressBar';
import { NavigationControls } from './NavigationControls';
import { useAssessment } from '../../context/useAssessment';

interface AssessmentLayoutProps {
  children: React.ReactNode;
}

export const AssessmentLayout: React.FC<AssessmentLayoutProps> = ({ children }) => {
  const { resetAssessment, state } = useAssessment();

  const handleStartOver = () => {
    if (window.confirm('Are you sure you want to start over? This will clear your current answers.')) {
      resetAssessment();
    }
  };

  if (state.isCompleted) {
    return (
      <div className="assessment-layout dashboard-mode">
        <main className="dashboard-main-content">
          {children}
        </main>
      </div>
    );
  }

  return (
    <div className="assessment-layout">

      <header className="assessment-header">
        <div className="brand-bar">
          <div className="brand-title-group">
            <h1>🌱 IrrigaSense</h1>
            <span className="badge">Farm Checkup</span>
          </div>

          {(state.history.length > 0 || state.isCompleted) && (
            <button
              type="button"
              className="start-over-btn"
              onClick={handleStartOver}
              title="Clear draft and start from beginning"
            >
              ↺ Start Over
            </button>
          )}
        </div>
        <ProgressBar />
      </header>

      <main className="assessment-content">
        {children}
      </main>

      <NavigationControls />
    </div>
  );
};
