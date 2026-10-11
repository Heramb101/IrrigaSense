import React, { createContext, useState, useEffect, useCallback } from 'react';
import type {
  User,
  AuthContextType,
  LoginCredentials,
  RegisterCredentials,
} from '../types/auth';
import { authApi } from '../services/authApi';

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [csrfToken, setCsrfToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  /**
   * Check backend session status on startup
   */
  const checkSession = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await authApi.getMe();
      setUser(data.user);
      setCsrfToken(data.csrf_token);
    } catch {
      // Unauthenticated visitor or expired session — safe clean initial state
      setUser(null);
      setCsrfToken(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    checkSession();
  }, [checkSession]);

  /**
   * Log in user with username and password
   */
  const login = async (credentials: LoginCredentials): Promise<void> => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await authApi.login(credentials);
      setUser(data.user);
      setCsrfToken(data.csrf_token);
    } catch (err: any) {
      const message = err?.message || 'Login failed';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Register a new user account
   */
  const register = async (credentials: RegisterCredentials): Promise<void> => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await authApi.register(credentials);
      setUser(data.user);
      setCsrfToken(data.csrf_token);
    } catch (err: any) {
      const message = err?.message || 'Registration failed';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Invalidate server session and clear user state
   */
  const logout = async (): Promise<void> => {
    try {
      setIsLoading(true);
      await authApi.logout(csrfToken);
    } catch {
      // Even if server request fails, clear local React session state
    } finally {
      setUser(null);
      setCsrfToken(null);
      setError(null);
      setIsLoading(false);
    }
  };

  const clearError = () => {
    setError(null);
  };

  const refreshUser = async (): Promise<User | null> => {
    try {
      const data = await authApi.getMe();
      setUser(data.user);
      setCsrfToken(data.csrf_token);
      return data.user;
    } catch {
      setUser(null);
      setCsrfToken(null);
      return null;
    }
  };

  const contextValue: AuthContextType = {
    user,
    csrfToken,
    isAuthenticated: Boolean(user),
    isLoading,
    error,
    login,
    register,
    logout,
    clearError,
    refreshUser,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};
