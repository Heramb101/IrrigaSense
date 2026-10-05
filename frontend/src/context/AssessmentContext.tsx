import React, { useEffect, useState, useMemo, useCallback } from 'react';
import type { AssessmentCreate, AssessmentData } from '../types/assessment';
import {
  type QuestionId,
  ASSESSMENT_CONFIG,
  ASSESSMENT_SECTIONS,
  QUESTION_SEQUENCE,
  getNextActiveQuestionId,
  isQuestionActive,
  validateAssessmentStep,
} from '../assessment/assessmentConfig';
import {
  type AssessmentState,
  INITIAL_ASSESSMENT_STATE,
} from '../assessment/assessmentState';
import {
  AssessmentContext,
  type AssessmentContextValue,
  type FinalSubmissionResult,
} from './assessmentContextDef';

export type { AssessmentContextValue, FinalSubmissionResult };

const STORAGE_KEY = 'irrigasense_assessment_draft';

function loadInitialState(): AssessmentState {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      const parsed = JSON.parse(saved);
      if (parsed && parsed.data && parsed.currentQuestionId) {
        return parsed;
      }
    }
  } catch {
    // Fall back to clean default if local storage corrupted or unavailable
  }
  return INITIAL_ASSESSMENT_STATE;
}

export const AssessmentProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, setState] = useState<AssessmentState>(loadInitialState);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [finalSubmission, setFinalSubmission] = useState<FinalSubmissionResult | null>(null);

  // Persistence effect: saves draft on state change
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch {
      // Storage quota or privacy mode handling
    }
  }, [state]);

  const currentQuestionDefinition = useMemo(() => {
    return ASSESSMENT_CONFIG[state.currentQuestionId];
  }, [state.currentQuestionId]);

  const currentSectionMetadata = useMemo(() => {
    if (currentQuestionDefinition) {
      return ASSESSMENT_SECTIONS[currentQuestionDefinition.section];
    }
    return undefined;
  }, [currentQuestionDefinition]);

  // Compute active sequence dynamically
  const activeQuestions = useMemo(() => {
    return QUESTION_SEQUENCE.filter((id) => isQuestionActive(id, state.data, ASSESSMENT_CONFIG));
  }, [state.data]);

  const progress = useMemo(() => {
    // Only count active assessment questions (exclude 'REVIEW') for step display
    const activeQuestionsExcludingReview = activeQuestions.filter((id) => id !== 'REVIEW');
    const totalActiveSteps = activeQuestionsExcludingReview.length;
    const isReview = state.currentQuestionId === 'REVIEW';

    let currentStepNumber = 1;
    if (isReview) {
      currentStepNumber = totalActiveSteps;
    } else {
      const activeIndex = activeQuestionsExcludingReview.indexOf(
        state.currentQuestionId as Exclude<QuestionId, 'REVIEW'>
      );
      currentStepNumber = activeIndex >= 0 ? activeIndex + 1 : 1;
    }

    const percent = isReview
      ? 100
      : Math.round((currentStepNumber / totalActiveSteps) * 100);

    return {
      currentStepNumber,
      totalActiveSteps,
      percent,
    };
  }, [activeQuestions, state.currentQuestionId]);

  const canGoBack = state.history.length > 0 && !state.isCompleted;
  const canGoNext = state.currentQuestionId !== 'REVIEW' && !state.isCompleted;
  const canReturnToReview =
    (Boolean(state.hasReachedReview) || state.history.includes('REVIEW')) &&
    state.currentQuestionId !== 'REVIEW' &&
    !state.isCompleted;

  const clearValidationError = useCallback(() => {
    setValidationError(null);
  }, []);

  const updateSectionData = useCallback(
    (section: keyof AssessmentData | string, updates: any) => {
      setValidationError(null);
      setState((prev) => {
        const nextData: AssessmentData = { ...prev.data };

        if (section === 'location') {
          const locUpdates = typeof updates === 'object' ? updates : {};
          nextData.location = {
            ...nextData.location,
            ...locUpdates,
          };
          nextData.latitude = nextData.location.latitude;
          nextData.longitude = nextData.location.longitude;
          nextData.place_name = nextData.location.place_name || nextData.location.location_name || '';
        } else if (section === 'crop') {
          if (typeof updates === 'string') {
            nextData.crop = updates;
          } else if (updates && typeof updates === 'object') {
            nextData.crop = updates.current_crop_id || updates.crop || '';
          }
        } else if (section === 'planting_date') {
          if (typeof updates === 'string') {
            nextData.planting_date = updates;
          } else if (updates && typeof updates === 'object') {
            nextData.planting_date = updates.planting_date || '';
          }
        } else if (section === 'farm_size') {
          if (typeof updates === 'string') {
            nextData.farm_size = updates;
          } else if (updates && typeof updates === 'object') {
            nextData.farm_size = updates.farm_size || updates.size_range || '';
          }
        } else if (section === 'irrigation_method') {
          if (typeof updates === 'string') {
            nextData.irrigation_method = updates;
          } else if (updates && typeof updates === 'object') {
            nextData.irrigation_method = updates.irrigation_method || updates.method || '';
          }
        } else if (section === 'water_availability') {
          if (typeof updates === 'string') {
            nextData.water_availability = updates;
          } else if (updates && typeof updates === 'object') {
            nextData.water_availability = updates.water_availability || updates.water_reliability || '';
          }
        } else {
          // Direct field assignment or legacy nested field
          (nextData as any)[section] = updates;
        }

        return {
          ...prev,
          data: nextData,
          lastSavedAt: new Date().toISOString(),
        };
      });
    },
    []
  );

  /**
   * Validates and advances to next active question.
   */
  const goToNext = useCallback((): boolean => {
    const validation = validateAssessmentStep(state.currentQuestionId, state.data);
    if (!validation.isValid) {
      setValidationError(validation.errorMessage || 'Please complete this question to continue.');
      return false;
    }

    setValidationError(null);

    const nextQuestionId = getNextActiveQuestionId(state.currentQuestionId, state.data);
    if (!nextQuestionId) {
      return false;
    }

    setState((prev) => ({
      ...prev,
      hasReachedReview: prev.hasReachedReview || nextQuestionId === 'REVIEW',
      history: [...prev.history, prev.currentQuestionId],
      currentQuestionId: nextQuestionId,
    }));
    return true;
  }, [state.currentQuestionId, state.data]);

  /**
   * Returns to previous question using history stack.
   */
  const goToPrevious = useCallback(() => {
    if (state.history.length === 0) return;
    setValidationError(null);

    setState((prev) => {
      const newHistory = [...prev.history];
      const previousQuestionId = newHistory.pop();
      if (!previousQuestionId) return prev;

      return {
        ...prev,
        history: newHistory,
        currentQuestionId: previousQuestionId,
      };
    });
  }, [state.history]);

  const goToQuestion = useCallback((questionId: QuestionId) => {
    setValidationError(null);
    setState((prev) => ({
      ...prev,
      history: [...prev.history, prev.currentQuestionId],
      currentQuestionId: questionId,
    }));
  }, []);

  /**
   * Submits the complete assessment. Formats the data into the AssessmentCreate contract.
   */
  const submitAssessment = useCallback((): boolean => {
    // Validate required fields
    if (!state.data.location.latitude || !state.data.location.longitude) {
      setValidationError('Please select and confirm your farm location.');
      return false;
    }
    const crop = typeof state.data.crop === 'string' ? state.data.crop : (state.data.crop as any)?.current_crop_id;
    if (!crop || crop.trim() === '') {
      setValidationError('Please select your current crop.');
      return false;
    }

    const loc = state.data.location;
    const cropVal = typeof state.data.crop === 'string' ? state.data.crop : (state.data.crop as any)?.current_crop_id || '';
    const plantingDate = state.data.planting_date || '';
    const farmSize = state.data.farm_size || '';
    const irrigationMethod = state.data.irrigation_method || '';
    const waterAvailability = state.data.water_availability || '';

    const payload: AssessmentCreate = {
      farm_id: 1, // Default development farm ID
      assessment_version: '2.0',
      latitude: loc.latitude,
      longitude: loc.longitude,
      place_name: loc.place_name || loc.location_name || '',
      crop: cropVal,
      planting_date: plantingDate,
      farm_size: farmSize,
      irrigation_method: irrigationMethod,
      water_availability: waterAvailability,
      data: {
        latitude: loc.latitude,
        longitude: loc.longitude,
        place_name: loc.place_name || loc.location_name || '',
        location: {
          latitude: loc.latitude,
          longitude: loc.longitude,
          place_name: loc.place_name || loc.location_name || '',
          location_confirmed: loc.location_confirmed,
        },
        crop: cropVal,
        planting_date: plantingDate,
        farm_size: farmSize,
        irrigation_method: irrigationMethod,
        water_availability: waterAvailability,
      },
    };

    setFinalSubmission({
      submittedAt: new Date().toISOString(),
      payload,
    });

    setState((prev) => ({
      ...prev,
      isCompleted: true,
      isSubmitting: false,
    }));

    return true;
  }, [state.data]);

  const resetAssessment = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setValidationError(null);
    setFinalSubmission(null);
    setState(INITIAL_ASSESSMENT_STATE);
  }, []);

  const returnToReview = useCallback(() => {
    setValidationError(null);
    setState((prev) => ({
      ...prev,
      history: [...prev.history, prev.currentQuestionId],
      currentQuestionId: 'REVIEW',
    }));
  }, []);

  const value = useMemo(
    () => ({
      state,
      currentQuestionDefinition,
      currentSectionMetadata,
      validationError,
      finalSubmission,
      progress,
      canGoBack,
      canGoNext,
      canReturnToReview,
      clearValidationError,
      updateSectionData,
      goToNext,
      goToPrevious,
      goToQuestion,
      returnToReview,
      submitAssessment,
      resetAssessment,
    }),
    [
      state,
      currentQuestionDefinition,
      currentSectionMetadata,
      validationError,
      finalSubmission,
      progress,
      canGoBack,
      canGoNext,
      canReturnToReview,
      clearValidationError,
      updateSectionData,
      goToNext,
      goToPrevious,
      goToQuestion,
      returnToReview,
      submitAssessment,
      resetAssessment,
    ]
  );

  return <AssessmentContext.Provider value={value}>{children}</AssessmentContext.Provider>;
};
