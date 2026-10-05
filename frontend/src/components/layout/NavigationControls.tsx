import { useAssessment } from '../../context/useAssessment';

export const NavigationControls: React.FC = () => {
  const {
    state,
    canGoBack,
    canGoNext,
    canReturnToReview,
    validationError,
    goToNext,
    goToPrevious,
    returnToReview,
  } = useAssessment();

  // If completed or on Review screen, standard bottom continue button is hidden
  if (state.isCompleted || state.currentQuestionId === 'REVIEW') {
    return null;
  }

  const isNextToReview = state.currentQuestionId === 'Q6';
  const nextLabel = isNextToReview ? 'Review Answers →' : 'Continue →';

  return (
    <footer className="navigation-controls-wrapper">
      {validationError && (
        <div className="validation-error-banner" role="alert">
          <span className="error-icon">⚠️</span>
          <span className="error-text">{validationError}</span>
        </div>
      )}

      <div className="navigation-buttons-row">
        <button
          type="button"
          className="btn btn-secondary"
          onClick={goToPrevious}
          disabled={!canGoBack}
          aria-label="Previous question"
        >
          ← Back
        </button>

        {canReturnToReview && (
          <button
            type="button"
            className="btn btn-outline"
            onClick={returnToReview}
            aria-label="Return directly to review summary"
            title="Return to review screen"
          >
            📋 Return to Review
          </button>
        )}

        <button
          type="button"
          className="btn btn-primary"
          onClick={goToNext}
          disabled={!canGoNext}
          aria-label="Continue to next question"
        >
          {nextLabel}
        </button>
      </div>
    </footer>
  );
};
