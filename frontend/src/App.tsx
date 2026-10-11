import React from 'react';
import { AuthProvider } from './context/AuthContext';
import { useAuth } from './context/useAuth';
import { AssessmentProvider } from './context/AssessmentContext';
import { AssessmentLayout } from './components/layout/AssessmentLayout';
import { QuestionDispatcher } from './components/questions/QuestionDispatcher';
import { AuthScreen } from './components/auth/AuthScreen';

const AppContent: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="auth-loading-screen" role="status" aria-live="polite">
        <div className="auth-loading-card">
          <div className="loading-brand-icon">🌱</div>
          <h2 className="loading-brand-title">IrrigaSense</h2>
          <div className="loading-spinner-wrapper">
            <div className="spinner-ring"></div>
          </div>
          <p className="loading-text">Verifying secure farmer session...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <AuthScreen />;
  }

  return (
    <AssessmentProvider>
      <AssessmentLayout>
        <QuestionDispatcher />
      </AssessmentLayout>
    </AssessmentProvider>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

export default App;
