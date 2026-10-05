import { createContext } from 'react';
import type { AssessmentCreate, AssessmentData } from '../types/assessment';
import type { QuestionId, QuestionDefinition, SectionMetadata } from '../assessment/assessmentConfig';
import type { AssessmentState } from '../assessment/assessmentState';

export interface FinalSubmissionResult {
  submittedAt: string;
  payload: AssessmentCreate;
}

export interface AssessmentContextValue {
  state: AssessmentState;
  currentQuestionDefinition?: QuestionDefinition;
  currentSectionMetadata?: SectionMetadata;
  validationError: string | null;
  finalSubmission: FinalSubmissionResult | null;
  progress: {
    currentStepNumber: number;
    totalActiveSteps: number;
    percent: number;
  };
  canGoBack: boolean;
  canGoNext: boolean;
  canReturnToReview: boolean;
  clearValidationError: () => void;
  updateSectionData: (
    section: keyof AssessmentData | string,
    data: any
  ) => void;
  goToNext: () => boolean;
  goToPrevious: () => void;
  goToQuestion: (questionId: QuestionId) => void;
  returnToReview: () => void;
  submitAssessment: () => boolean;
  resetAssessment: () => void;
}

export const AssessmentContext = createContext<AssessmentContextValue | null>(null);
