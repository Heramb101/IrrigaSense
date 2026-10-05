import React from 'react';
import { AssessmentProvider } from './context/AssessmentContext';
import { AssessmentLayout } from './components/layout/AssessmentLayout';
import { QuestionDispatcher } from './components/questions/QuestionDispatcher';

export const App: React.FC = () => {
  return (
    <AssessmentProvider>
      <AssessmentLayout>
        <QuestionDispatcher />
      </AssessmentLayout>
    </AssessmentProvider>
  );
};

export default App;
