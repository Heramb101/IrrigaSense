import React, { useState } from 'react';
import { useAuth } from '../../context/useAuth';

interface LoginFormProps {
  onSwitchToRegister: () => void;
}

export const LoginForm: React.FC<LoginFormProps> = ({ onSwitchToRegister }) => {
  const { login, isLoading, error, clearError } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<{ username?: string; password?: string }>({});

  const validate = (): boolean => {
    const errors: { username?: string; password?: string } = {};
    const trimmedUser = username.trim();

    if (!trimmedUser) {
      errors.username = 'Username is required';
    }

    if (!password) {
      errors.password = 'Password is required';
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
      await login({
        username: username.trim().toLowerCase(),
        password,
      });
    } catch {
      // Auth error is captured in AuthContext
    }
  };

  return (
    <div className="auth-card">
      <div className="auth-card-header">
        <h2 className="auth-title">Farmer Sign In</h2>
        <p className="auth-subtitle">
          Access your farm assessments, crop advisories, and adaptive irrigation history.
        </p>
      </div>

      {error && (
        <div className="auth-error-banner" role="alert">
          <span className="auth-error-icon">⚠️</span>
          <span className="auth-error-text">{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="auth-form" noValidate>
        <div className={`form-group ${fieldErrors.username ? 'has-error' : ''}`}>
          <label htmlFor="login-username" className="form-label">
            Username <span className="required-star">*</span>
          </label>
          <div className="input-wrapper">
            <input
              id="login-username"
              type="text"
              name="username"
              value={username}
              onChange={(e) => {
                setUsername(e.target.value);
                if (fieldErrors.username) {
                  setFieldErrors((prev) => ({ ...prev, username: undefined }));
                }
              }}
              placeholder="e.g. farmer_ramesh"
              autoComplete="username"
              autoCapitalize="none"
              spellCheck="false"
              className="form-input"
              disabled={isLoading}
              aria-invalid={Boolean(fieldErrors.username)}
              aria-describedby={fieldErrors.username ? 'login-username-error' : undefined}
            />
          </div>
          {fieldErrors.username && (
            <span id="login-username-error" className="field-error-message">
              {fieldErrors.username}
            </span>
          )}
        </div>

        <div className={`form-group ${fieldErrors.password ? 'has-error' : ''}`}>
          <label htmlFor="login-password" className="form-label">
            Password <span className="required-star">*</span>
          </label>
          <div className="input-wrapper password-input-wrapper">
            <input
              id="login-password"
              type={showPassword ? 'text' : 'password'}
              name="password"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                if (fieldErrors.password) {
                  setFieldErrors((prev) => ({ ...prev, password: undefined }));
                }
              }}
              placeholder="Enter your password"
              autoComplete="current-password"
              className="form-input"
              disabled={isLoading}
              aria-invalid={Boolean(fieldErrors.password)}
              aria-describedby={fieldErrors.password ? 'login-password-error' : undefined}
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
            <span id="login-password-error" className="field-error-message">
              {fieldErrors.password}
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
              <span className="spinner-dot"></span> Signing in...
            </span>
          ) : (
            'Sign In to IrrigaSense'
          )}
        </button>
      </form>

      <div className="auth-card-footer">
        <p className="auth-switch-text">
          Don't have an account yet?{' '}
          <button
            type="button"
            className="auth-switch-link"
            onClick={() => {
              clearError();
              onSwitchToRegister();
            }}
          >
            Create Farmer Account
          </button>
        </p>
      </div>
    </div>
  );
};
