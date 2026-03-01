import type { TokenClaims } from './api';

/**
 * Active user session state
 */
export interface Session {
  accessToken: string;
  refreshToken: string;
  claims: TokenClaims;
  issuedAt: number; // timestamp in ms
  expiresAt: number; // timestamp in ms
}

/**
 * Session status
 */
export type SessionStatus = 'active' | 'expired' | 'invalid' | 'none';

/**
 * Decoded session info for display
 */
export interface SessionInfo {
  userId: string;
  tenantId: string;
  role: string;
  expiresAt: Date;
  status: SessionStatus;
  issuedAt: Date;
  expirationMinutes: number;
}

/**
 * Login form data
 */
export interface LoginFormData {
  email: string;
  password: string;
  rememberMe?: boolean;
}

/**
 * Refresh token result
 */
export interface RefreshTokenResult {
  success: boolean;
  rotated: boolean;
  newAccessToken: string;
  newExpiresAt: number;
  error?: {
    code: string;
    message: string;
  };
}

/**
 * Auth context value
 */
export interface AuthContextValue {
  session: Session | null;
  sessionInfo: SessionInfo | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  refresh: () => Promise<RefreshTokenResult>;
  revoke: () => Promise<void>;
  logout: () => void;
}
