'use client';

import { createContext, useEffect, useState, useCallback } from 'react';
import type { Session, SessionInfo, AuthContextValue, RefreshTokenResult } from '@/types/session';
import {
  createAuthService,
  getSessionInfo,
  clearStoredSession,
  retrieveStoredSession,
} from '@/lib/auth';
import { createApiClient, getApiBaseUrl } from '@/lib/api';

/**
 * Auth context
 */
export const AuthContext = createContext<AuthContextValue | null>(null);

/**
 * Auth provider component
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [sessionInfo, setSessionInfo] = useState<SessionInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize API client and auth service
  const apiClient = createApiClient(
    getApiBaseUrl(),
    () => session?.accessToken ?? null,
    () => {
      // Handle unauthorized - trigger logout
      logout();
    }
  );
  const authService = createAuthService(apiClient);

  // Restore session from storage on mount
  useEffect(() => {
    const storedSession = retrieveStoredSession();
    if (storedSession) {
      setSession(storedSession);
      setSessionInfo(getSessionInfo(storedSession));
    }
    setIsLoading(false);
  }, []);

  // Update session info when session changes
  useEffect(() => {
    if (session) {
      setSessionInfo(getSessionInfo(session));
    } else {
      setSessionInfo(null);
    }
  }, [session]);

  /**
   * Login
   */
  const login = useCallback(
    async (email: string, password: string) => {
      setIsLoading(true);
      try {
        const newSession = await authService.login(email, password);
        setSession(newSession);
      } finally {
        setIsLoading(false);
      }
    },
    [authService]
  );

  /**
   * Refresh token
   */
  const refresh = useCallback(async (): Promise<RefreshTokenResult> => {
    if (!session) {
      return {
        success: false,
        rotated: false,
        newAccessToken: '',
        newExpiresAt: 0,
        error: {
          code: 'no_session',
          message: 'No active session',
        },
      };
    }

    try {
      const newSession = await authService.refreshSession(session);
      setSession(newSession);

      return {
        success: true,
        rotated: true,
        newAccessToken: newSession.accessToken,
        newExpiresAt: newSession.expiresAt,
      };
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Refresh failed';

      return {
        success: false,
        rotated: false,
        newAccessToken: '',
        newExpiresAt: 0,
        error: {
          code:
            message.includes('reuse') || message.includes('compromised')
              ? 'refresh_token_reuse'
              : 'refresh_failed',
          message,
        },
      };
    }
  }, [session, authService]);

  /**
   * Revoke session
   */
  const revoke = useCallback(async () => {
    if (!sessionInfo) {
      return;
    }

    try {
      await authService.revokeSession(sessionInfo.userId, sessionInfo.tenantId);
      logout();
    } catch (error) {
      // Even if revoke fails, clear local session
      logout();
    }
  }, [sessionInfo, authService]);

  /**
   * Logout
   */
  const logout = useCallback(() => {
    clearStoredSession();
    setSession(null);
    setSessionInfo(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        session,
        sessionInfo,
        isLoading,
        isAuthenticated: !!session && sessionInfo?.status === 'active',
        login,
        refresh,
        revoke,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
