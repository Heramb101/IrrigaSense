import React, { useState } from 'react';
import { LoginForm } from './LoginForm';
import { RegisterForm } from './RegisterForm';

export const AuthScreen: React.FC = () => {
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');

  return (
    <div className="auth-screen-container">
      <div className="auth-screen-content">
        <header className="auth-brand-header">
          <div className="auth-brand-logo">
            <span className="brand-leaf-icon">🌱</span>
            <span className="brand-logo-text">IrrigaSense</span>
          </div>
          <span className="auth-brand-badge">Precision Agriculture · ANFIS AI</span>
          <p className="auth-brand-tagline">
            Intelligent Soil Moisture Forecasting & Agronomic Irrigation Scheduling
          </p>
        </header>

        <main className="auth-main-area">
          {authMode === 'login' ? (
            <LoginForm onSwitchToRegister={() => setAuthMode('register')} />
          ) : (
            <RegisterForm onSwitchToLogin={() => setAuthMode('login')} />
          )}
        </main>

        <footer className="auth-screen-footer">
          <p className="footer-meta">
            IrrigaSense Decision Support System · ICAR-VNR Agronomic Standards · 5-Input ANFIS Model
          </p>
        </footer>
      </div>
    </div>
  );
};
