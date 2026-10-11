import React, { useState } from 'react';
import { useAuth } from '../../context/useAuth';

interface RegisterFormProps {
  onSwitchToLogin: () => void;
}

export const RegisterForm: React.FC<RegisterFormProps> = ({ onSwitchToLogin }) => {
  const { register, isLoading, error, clearError } = useAuth();
  const [name, setName] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<{
    name?: string;
    username?: string;
    password?: string;
    confirmPassword?: string;
  }>({});

  const validate = (): boolean => {
    const errors: {
      name?: string;
      username?: string;
      password?: string;
      confirmPassword?: string;
    } = {};

    const trimmedUser = username.trim();
    if (!trimmedUser) {
      errors.username = 'Username is required';
    } else if (trimmedUser.length < 3) {
      errors.username = 'Username must be at least 3 characters';
    } else if (trimmedUser.length > 30) {
      errors.username = 'Username cannot exceed 30 characters';
    } else if (!/^[a-zA-Z0-9_]+$/.test(trimmedUser)) {
      errors.username = 'Username can only contain letters, numbers, and underscores';
    }

    if (!password) {
      errors.password = 'Password is required';
    } else if (password.length < 8) {
      errors.password = 'Password must be at least 8 characters';
    } else if (password.length > 128) {
      errors.password = 'Password cannot exceed 128 characters';
    }

    if (!confirmPassword) {
      errors.confirmPassword = 'Please confirm your password';
    } else if (password !== confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();

    if (!validate()) {
      return;
    }

    try {
      await register({
        username: username.trim().toLowerCase(),
        password,
        name: name.trim() || undefined,
      });
    } catch {
      // Auth error is captured in AuthContext
    }
  };

  return (
    <div className="auth-card">
      <div className="auth-card-header">
        <h2 className="auth-title">Create Farmer Account</h2>
        <p className="auth-subtitle">
          Join IrrigaSense to calculate precision irrigation schedules and save farm history.
        </p>
      </div>

      {error && (
        <div className="auth-error-banner" role="alert">
          <span className="auth-error-icon">⚠️</span>
          <span className="auth-error-text">{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="auth-form" noValidate>
        <div className="form-group">
          <label htmlFor="reg-name" className="form-label">
            Full Name <span className="optional-tag">(Optional)</span>
          </label>
          <div className="input-wrapper">
            <input
              id="reg-name"
              type="text"
              name="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Ramesh Patel"
              autoComplete="name"
              className="form-input"
              disabled={isLoading}
            />
          </div>
        </div>

        <div className={`form-group ${fieldErrors.username ? 'has-error' : ''}`}>
          <label htmlFor="reg-username" className="form-label">
            Username <span className="required-star">*</span>
          </label>
          <div className="input-wrapper">
            <input
              id="reg-username"
              type="text"
              name="username"
              value={username}
              onChange={(e) => {
                setUsername(e.target.value);
                if (fieldErrors.username) {
                  setFieldErrors((prev) => ({ ...prev, username: undefined }));
                }
              }}
              placeholder="Choose a unique username (e.g. farmer_ramesh)"
              autoComplete="username"
              autoCapitalize="none"
              spellCheck="false"
              className="form-input"
              disabled={isLoading}
              aria-invalid={Boolean(fieldErrors.username)}
              aria-describedby={fieldErrors.username ? 'reg-username-error' : undefined}
            />
          </div>
          {fieldErrors.username && (
            <span id="reg-username-error" className="field-error-message">
              {fieldErrors.username}
            </span>
          )}
        </div>

        <div className={`form-group ${fieldErrors.password ? 'has-error' : ''}`}>
          <label htmlFor="reg-password" className="form-label">
            Password <span className="required-star">*</span>
          </label>
          <div className="input-wrapper password-input-wrapper">
            <input
              id="reg-password"
              type={showPassword ? 'text' : 'password'}
              name="password"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                if (fieldErrors.password) {
                  setFieldErrors((prev) => ({ ...prev, password: undefined }));
                }
              }}
              placeholder="Minimum 8 characters"
              autoComplete="new-password"
              className="form-input"
              disabled={isLoading}
              aria-invalid={Boolean(fieldErrors.password)}
              aria-describedby={fieldErrors.password ? 'reg-password-error' : undefined}
            />
            <button
              type="button"
              className="password-toggle-btn"
              onClick={() => setShowPassword(!showPassword)}
              title={showPassword ? 'Hide password' : 'Show password'}
              aria-label={showPassword ? 'Hide password' : 'Show password'}
              tabIndex={0}
            >
              {showPassword ? '🙈' : '👁️'}
            </button>
          </div>
          {fieldErrors.password && (
            <span id="reg-password-error" className="field-error-message">
              {fieldErrors.password}
            </span>
          )}
        </div>

        <div className={`form-group ${fieldErrors.confirmPassword ? 'has-error' : ''}`}>
          <label htmlFor="reg-confirm-password" className="form-label">
            Confirm Password <span className="required-star">*</span>
          </label>
          <div className="input-wrapper password-input-wrapper">
            <input
              id="reg-confirm-password"
              type={showConfirmPassword ? 'text' : 'password'}
              name="confirmPassword"
              value={confirmPassword}
              onChange={(e) => {
                setConfirmPassword(e.target.value);
                if (fieldErrors.confirmPassword) {
                  setFieldErrors((prev) => ({ ...prev, confirmPassword: undefined }));
                }
              }}
              placeholder="Re-enter your password"
              autoComplete="new-password"
              className="form-input"
              disabled={isLoading}
              aria-invalid={Boolean(fieldErrors.confirmPassword)}
              aria-describedby={fieldErrors.confirmPassword ? 'reg-confirm-error' : undefined}
            />
            <button
              type="button"
              className="password-toggle-btn"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              title={showConfirmPassword ? 'Hide password' : 'Show password'}
              aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
              tabIndex={0}
            >
              {showConfirmPassword ? '🙈' : '👁️'}
            </button>
          </div>
          {fieldErrors.confirmPassword && (
            <span id="reg-confirm-error" className="field-error-message">
              {fieldErrors.confirmPassword}
            </span>
          )}
        </div>

        <button
          type="submit"
          className="auth-submit-btn"
          disabled={isLoading}
          aria-busy={isLoading}
        >
          {isLoading ? (
            <span className="btn-loading-content">
              <span className="spinner-dot"></span> Creating account...
            </span>
          ) : (
            'Create Account & Start'
          )}
        </button>
      </form>

      <div className="auth-card-footer">
        <p className="auth-switch-text">
          Already have an account?{' '}
          <button
            type="button"
            className="auth-switch-link"
            onClick={() => {
              clearError();
              onSwitchToLogin();
            }}
          >
            Sign In
          </button>
        </p>
      </div>
    </div>
  );
};
