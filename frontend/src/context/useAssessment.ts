import { useContext } from 'react';
import { AssessmentContext, type AssessmentContextValue } from './assessmentContextDef';

export const useAssessment = (): AssessmentContextValue => {
  const context = useContext(AssessmentContext);
  if (!context) {
    throw new Error('useAssessment must be used within an AssessmentProvider');
  }
  return context;
};

export default useAssessment;
