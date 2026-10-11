/**
 * IrrigaSense Authentication Types — Milestone 13B
 */

export interface User {
  id: number;
  username: string;
  name?: string | null;
  email?: string | null;
  created_at?: string | null;
}

export interface AuthResponse {
  user: User;
  csrf_token: string;
  message?: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterCredentials {
  username: string;
  password: string;
  name?: string;
  email?: string;
}

export interface MessageResponse {
  message: string;
}

export interface AuthContextType {
  user: User | null;
  csrfToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (credentials: RegisterCredentials) => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
  refreshUser: () => Promise<User | null>;
}
