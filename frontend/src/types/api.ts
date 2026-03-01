/**
 * Generic API response wrapper matching backend BaseResponse<T> contract
 */
export interface BaseResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}

/**
 * API Meta information from request
 */
export interface ApiMeta {
  requestId: string;
  durationMs: number;
  status: number;
}

/**
 * API response with metadata
 */
export interface ApiResult<T = unknown> extends BaseResponse<T> {
  meta: ApiMeta;
}

/**
 * Auth request/response types
 */
export interface AuthTokenRequest {
  user_id: string;
  role: string;
  tenant_id?: string;
}

export interface AuthTokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface AuthRefreshRequest {
  refresh_token: string;
}

export interface AuthRefreshResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  rotated: boolean;
}

export interface AuthRevokeRequest {
  user_id: string;
  tenant_id: string;
}

/**
 * JWT Token Claims (after decoding)
 */
export interface TokenClaims {
  sub: string; // user_id
  tenant_id: string;
  role: string;
  exp: number; // expiration timestamp in seconds
  iat: number; // issued at timestamp in seconds
}

/**
 * Health check response
 */
export interface HealthResponse {
  status: string;
}

/**
 * Error codes that can be returned by the API
 */
export const API_ERROR_CODES = {
  NETWORK_EXCEPTION: 'network_exception',
  INVALID_JSON: 'invalid_json',
  UNKNOWN_ERROR: 'unknown_error',
  OVER_CAPACITY: 'over_capacity',
  VALIDATION_ERROR: 'validation_error',
  UNAUTHORIZED: 'unauthorized',
  FORBIDDEN: 'forbidden',
  NOT_FOUND: 'not_found',
  CONFLICT: 'conflict',
  REFRESH_TOKEN_REUSE: 'refresh_token_reuse',
} as const;

export type ApiErrorCode = (typeof API_ERROR_CODES)[keyof typeof API_ERROR_CODES];
