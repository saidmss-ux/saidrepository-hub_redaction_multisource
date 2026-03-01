import type { TokenClaims, Session, SessionInfo, SessionStatus } from '@/types/session';
import type {
  AuthTokenResponse,
  AuthRefreshResponse,
  AuthRefreshRequest,
  AuthRevokeRequest,
} from '@/types/api';
import type { ApiClient } from './api';

/**
 * Decode JWT token and extract claims
 */
export function decodeToken(token: string): TokenClaims | null {
  try {
    // JWT format: header.payload.signature
    const parts = token.split('.');
    if (parts.length !== 3) {
      return null;
    }

    // Decode payload (add padding if necessary)
    const payload = parts[1];
    const paddedPayload = payload + '='.repeat((4 - (payload.length % 4)) % 4);
    const decoded = atob(paddedPayload);
    const claims = JSON.parse(decoded);

    return claims as TokenClaims;
  } catch {
    return null;
  }
}

/**
 * Check if token is expired
 */
export function isTokenExpired(token: string): boolean {
  const claims = decodeToken(token);
  if (!claims) {
    return true;
  }

  // exp is in seconds, Date.now() is in milliseconds
  const now = Math.floor(Date.now() / 1000);
  return claims.exp <= now;
}

/**
 * Get token expiration timestamp in milliseconds
 */
export function getTokenExpirationMs(token: string): number | null {
  const claims = decodeToken(token);
  if (!claims) {
    return null;
  }

  // Convert from seconds to milliseconds
  return claims.exp * 1000;
}

/**
 * Create session from auth response
 */
export function createSessionFromResponse(
  response: AuthTokenResponse | AuthRefreshResponse,
  baseUrl?: string
): Session {
  const claims = decodeToken(response.access_token);
  if (!claims) {
    throw new Error('Failed to decode access token');
  }

  const now = Date.now();
  const expiresAt = (claims.exp * 1000);

  return {
    accessToken: response.access_token,
    refreshToken: response.refresh_token,
    claims,
    issuedAt: now,
    expiresAt,
  };
}

/**
 * Get session info for display
 */
export function getSessionInfo(session: Session): SessionInfo {
  const expiresAt = new Date(session.expiresAt);
  const issuedAt = new Date(session.issuedAt);
  const now = Date.now();

  let status: SessionStatus = 'active';
  if (now > session.expiresAt) {
    status = 'expired';
  }

  const expirationMinutes = Math.max(0, Math.ceil((session.expiresAt - now) / 1000 / 60));

  return {
    userId: session.claims.sub,
    tenantId: session.claims.tenant_id,
    role: session.claims.role,
    expiresAt,
    issuedAt,
    status,
    expirationMinutes,
  };
}

/**
 * Store tokens in session storage and cookies
 * Note: We avoid localStorage for refresh tokens for security reasons
 * Access token is kept in memory (via React state)
 * Refresh token can optionally be stored in httpOnly cookie (server-side set)
 */
export function storeTokens(session: Session): void {
  // Store in sessionStorage for recovery on page reload
  if (typeof window !== 'undefined') {
    try {
      sessionStorage.setItem('session', JSON.stringify(session));
    } catch {
      // Storage quota exceeded or disabled, continue with memory-only
    }
  }
}

/**
 * Retrieve stored session from sessionStorage
 */
export function retrieveStoredSession(): Session | null {
  if (typeof window === 'undefined') {
    return null;
  }

  try {
    const stored = sessionStorage.getItem('session');
    if (!stored) {
      return null;
    }

    const session = JSON.parse(stored) as Session;

    // Validate session structure
    if (!session.accessToken || !session.claims || !session.expiresAt) {
      return null;
    }

    return session;
  } catch {
    return null;
  }
}

/**
 * Clear stored session
 */
export function clearStoredSession(): void {
  if (typeof window === 'undefined') {
    return;
  }

  try {
    sessionStorage.removeItem('session');
  } catch {
    // Ignore errors
  }
}

/**
 * Auth service for API calls
 */
export class AuthService {
  constructor(private apiClient: ApiClient) {}

  /**
   * Login with email and password
   * Note: In real implementation, this would be POST /auth/login with credentials
   * For now, we use POST /auth/token as per the backend router
   */
  async login(email: string, password: string, tenantId?: string): Promise<Session> {
    // In real scenario, credentials would be sent to backend
    // For this demo, we're assuming backend validates and returns tokens
    const result = await this.apiClient.post<AuthTokenResponse>('/auth/token', {
      user_id: email, // Using email as user_id for demo
      role: 'user',
      tenant_id: tenantId,
    });

    if (!result.success || !result.data) {
      throw new Error(result.error?.message || 'Login failed');
    }

    const session = createSessionFromResponse(result.data);
    storeTokens(session);

    // In a real app, also set httpOnly cookie via server
    // This would require a server action or middleware
    return session;
  }

  /**
   * Refresh access token
   */
  async refreshSession(session: Session): Promise<Session> {
    const request: AuthRefreshRequest = {
      refresh_token: session.refreshToken,
    };

    const result = await this.apiClient.post<AuthRefreshResponse>('/auth/refresh', request);

    if (!result.success || !result.data) {
      throw new Error(result.error?.message || 'Token refresh failed');
    }

    // Check for refresh token reuse detection
    if (result.error?.code === 'refresh_token_reuse') {
      throw new Error('Refresh token reuse detected - session compromised');
    }

    const newSession = createSessionFromResponse(result.data);
    storeTokens(newSession);

    return newSession;
  }

  /**
   * Revoke user sessions
   */
  async revokeSession(userId: string, tenantId: string): Promise<void> {
    const request: AuthRevokeRequest = {
      user_id: userId,
      tenant_id: tenantId,
    };

    const result = await this.apiClient.post('/auth/revoke', request);

    if (!result.success) {
      throw new Error(result.error?.message || 'Session revocation failed');
    }

    clearStoredSession();
  }
}

/**
 * Create auth service instance
 */
export function createAuthService(apiClient: ApiClient): AuthService {
  return new AuthService(apiClient);
}
