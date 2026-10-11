import React, { useState } from 'react';
import { ProgressBar } from './ProgressBar';
import { NavigationControls } from './NavigationControls';
import { useAssessment } from '../../context/useAssessment';
import { useAuth } from '../../context/useAuth';
import { AssessmentHistoryView } from '../history/AssessmentHistoryView';
import type { AssessmentRead } from '../../types/assessment';

interface AssessmentLayoutProps {
  children: React.ReactNode;
}

export const AssessmentLayout: React.FC<AssessmentLayoutProps> = ({ children }) => {
  const { resetAssessment, loadDraftFromAssessment, state } = useAssessment();
  const { user, logout } = useAuth();
  const [currentView, setCurrentView] = useState<'checkup' | 'history'>('checkup');

  const handleStartOver = () => {
    if (window.confirm('Are you sure you want to start over? This will clear your current answers.')) {
      resetAssessment();
      setCurrentView('checkup');
    }
  };

  const handleLogout = async () => {
    if (window.confirm('Are you sure you want to sign out?')) {
      await logout();
    }
  };

  const handleReopenAssessment = (assessment: AssessmentRead) => {
    if (loadDraftFromAssessment) {
      loadDraftFromAssessment(assessment);
      setCurrentView('checkup');
    }
  };

  // If History view is active
  if (currentView === 'history') {
    return (
      <div className="assessment-layout history-mode">
        <header className="assessment-header">
          <div className="brand-bar">
            <div className="brand-title-group">
              <h1>🌱 IrrigaSense</h1>
              <span className="badge">Assessment History</span>
            </div>

            <div className="header-nav-tabs">
              <button
                type="button"
                className="nav-tab-btn"
                onClick={() => setCurrentView('checkup')}
                title="Go to farm checkup questionnaire"
              >
                🌱 Farm Checkup
              </button>
              <button
                type="button"
                className="nav-tab-btn active"
                onClick={() => setCurrentView('history')}
                title="View previous assessments"
              >
                📋 History
              </button>
            </div>

            <div className="header-actions-group">
              {user && (
                <div className="user-profile-badge">
                  <span className="user-avatar-icon">👤</span>
                  <span className="user-display-name" title={`Logged in as ${user.username}`}>
                    {user.name || user.username}
                  </span>
                  <button
                    type="button"
                    className="sign-out-btn"
                    onClick={handleLogout}
                    title="Sign out of account"
                  >
                    Sign Out
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        <main className="assessment-content history-content-area">
          <AssessmentHistoryView
            onStartNewAssessment={() => {
              resetAssessment();
              setCurrentView('checkup');
            }}
            onReopenAssessment={handleReopenAssessment}
          />
        </main>
      </div>
    );
  }

  // Dashboard Mode (Completed Assessment)
  if (state.isCompleted) {
    return (
      <div className="assessment-layout dashboard-mode">
        <header className="dashboard-app-header">
          <div className="dashboard-brand-row">
            <div className="brand-title-group">
              <span className="brand-logo-icon">🌱</span>
              <h1 className="brand-heading">IrrigaSense</h1>
              <span className="badge">Advisor Dashboard</span>
            </div>

            <div className="header-nav-tabs">
              <button
                type="button"
                className="nav-tab-btn active"
                onClick={() => setCurrentView('checkup')}
                title="Current Dashboard"
              >
                💧 Dashboard
              </button>
              <button
                type="button"
                className="nav-tab-btn"
                onClick={() => setCurrentView('history')}
                title="View previous assessments"
              >
                📋 History
              </button>
            </div>

            {user && (
              <div className="user-profile-badge">
                <span className="user-avatar-icon">👤</span>
                <span className="user-display-name" title={`Logged in as ${user.username}`}>
                  {user.name || user.username}
                </span>
                <button
                  type="button"
                  className="sign-out-btn"
                  onClick={handleLogout}
                  title="Sign out of account"
                >
                  Sign Out
                </button>
              </div>
            )}
          </div>
        </header>
        <main className="dashboard-main-content">
          {children}
        </main>
      </div>
    );
  }

  // Questionnaire Mode (In-Progress Assessment)
  return (
    <div className="assessment-layout">
      <header className="assessment-header">
        <div className="brand-bar">
          <div className="brand-title-group">
            <h1>🌱 IrrigaSense</h1>
            <span className="badge">Farm Checkup</span>
          </div>

          <div className="header-nav-tabs">
            <button
              type="button"
              className="nav-tab-btn active"
              onClick={() => setCurrentView('checkup')}
              title="Active farm checkup questionnaire"
            >
              🌱 Farm Checkup
            </button>
            <button
              type="button"
              className="nav-tab-btn"
              onClick={() => setCurrentView('history')}
              title="View saved assessment history"
            >
              📋 History
            </button>
          </div>

          <div className="header-actions-group">
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

            {user && (
              <div className="user-profile-badge">
                <span className="user-avatar-icon">👤</span>
                <span className="user-display-name" title={`Logged in as ${user.username}`}>
                  {user.name || user.username}
                </span>
                <button
                  type="button"
                  className="sign-out-btn"
                  onClick={handleLogout}
                  title="Sign out of account"
                >
                  Sign Out
                </button>
              </div>
            )}
          </div>
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
