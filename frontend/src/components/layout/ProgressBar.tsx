import { useAssessment } from '../../context/useAssessment';

export const ProgressBar: React.FC = () => {
  const { progress, currentSectionMetadata, state } = useAssessment();

  if (state.isCompleted) {
    return null;
  }

  const isReview = state.currentQuestionId === 'REVIEW';

  return (
    <div className="progress-container" aria-label="Assessment Progress">
      <div className="progress-header">
        <span className="section-title">
          {currentSectionMetadata ? currentSectionMetadata.title : 'Assessment'}
        </span>
        <span className="step-count">
          {isReview ? (
            'Final Step: Review'
          ) : (
            `Question ${progress.currentStepNumber} of ${progress.totalActiveSteps}`
          )}
        </span>
      </div>
      <div className="progress-bar-track">
        <div
          className="progress-bar-fill"
          style={{ width: `${progress.percent}%` }}
          role="progressbar"
          aria-valuenow={progress.percent}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
    </div>
  );
};
