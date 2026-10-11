import type {
  AuthResponse,
  LoginCredentials,
  RegisterCredentials,
  MessageResponse,
} from '../types/auth';

const API_BASE_URL =
  (typeof import.meta !== 'undefined' && (import.meta as any).env?.VITE_API_URL) ||
  'http://localhost:8000/api';

/**
 * Authentication API Service — Milestone 13B
 * Manages HTTP requests to FastAPI authentication endpoints:
 * - POST /api/auth/register
 * - POST /api/auth/login
 * - POST /api/auth/logout
 * - GET  /api/auth/me
 *
 * Uses credentials: 'include' so that HttpOnly session cookies are
 * properly transmitted and received cross-origin / same-origin.
 * Zero secrets or tokens are stored in browser storage.
 */
export const authApi = {
  /**
   * Register a new user account and receive session cookie
   */
  async register(credentials: RegisterCredentials): Promise<AuthResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      const detail = errorData?.detail || response.statusText || 'Registration failed';
      throw new Error(detail);
    }

    return response.json();
  },

  /**
   * Log in with username and password, receiving HttpOnly session cookie
   */
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      const detail = errorData?.detail || response.statusText || 'Invalid username or password';
      throw new Error(detail);
    }

    return response.json();
  },

  /**
   * Invalidate server session and clear HttpOnly cookie
   */
  async logout(csrfToken?: string | null): Promise<MessageResponse> {
    const headers: Record<string, string> = {
      'Accept': 'application/json',
    };
    if (csrfToken) {
      headers['X-CSRF-Token'] = csrfToken;
    }

    const response = await fetch(`${API_BASE_URL}/auth/logout`, {
      method: 'POST',
      headers,
      credentials: 'include',
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      const detail = errorData?.detail || response.statusText || 'Logout failed';
      throw new Error(detail);
    }

    return response.json();
  },

  /**
   * Retrieve currently authenticated user identity and CSRF token
   */
  async getMe(): Promise<AuthResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
      credentials: 'include',
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      const detail = errorData?.detail || response.statusText || 'Not authenticated';
      throw new Error(detail);
    }

    return response.json();
  },
};
