import React from 'react';

interface OptionCardProps {
  value: string;
  label: string;
  description?: string;
  icon?: string;
  selected: boolean;
  isMulti?: boolean;
  disabled?: boolean;
  onClick: (value: string) => void;
}

export const OptionCard: React.FC<OptionCardProps> = ({
  value,
  label,
  description,
  icon,
  selected,
  isMulti = false,
  disabled = false,
  onClick,
}) => {
  return (
    <div
      className={`option-card ${selected ? 'selected' : ''} ${disabled ? 'disabled' : ''}`}
      onClick={() => !disabled && onClick(value)}
      role="button"
      tabIndex={disabled ? -1 : 0}
      onKeyDown={(e) => {
        if (!disabled && (e.key === 'Enter' || e.key === ' ')) {
          e.preventDefault();
          onClick(value);
        }
      }}
      aria-pressed={selected}
    >
      <div className="option-card-indicator">
        {isMulti ? (
          <div className={`checkbox-box ${selected ? 'checked' : ''}`}>
            {selected && <span>✓</span>}
          </div>
        ) : (
          <div className={`radio-dot ${selected ? 'checked' : ''}`} />
        )}
      </div>

      {icon && <div className="option-card-icon">{icon}</div>}

      <div className="option-card-content">
        <h4 className="option-card-label">{label}</h4>
        {description && <p className="option-card-desc">{description}</p>}
      </div>
    </div>
  );
};
