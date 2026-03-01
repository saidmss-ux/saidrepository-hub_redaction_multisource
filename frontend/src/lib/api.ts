import type { ApiResult, BaseResponse } from '@/types/api';

/**
 * API Client configuration
 */
interface ApiClientConfig {
  baseUrl: string;
  timeoutMs?: number;
  getAccessToken?: () => string | null;
  onUnauthorized?: () => void;
  logger?: typeof console;
}

/**
 * Default request ID generator
 */
function generateRequestId(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `req_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

/**
 * API Client with fetch wrapper, timeout, and error handling
 */
export class ApiClient {
  private baseUrl: string;
  private timeoutMs: number;
  private getAccessToken: () => string | null;
  private onUnauthorized: () => void;
  private logger: typeof console;

  constructor(config: ApiClientConfig) {
    this.baseUrl = config.baseUrl;
    this.timeoutMs = config.timeoutMs ?? 8000;
    this.getAccessToken = config.getAccessToken ?? (() => null);
    this.onUnauthorized = config.onUnauthorized ?? (() => {});
    this.logger = config.logger ?? console;
  }

  /**
   * Perform API request with timeout and error handling
   */
  async request<T = unknown>(
    path: string,
    options?: {
      method?: string;
      body?: Record<string, unknown>;
      headers?: Record<string, string>;
      requestId?: string;
    }
  ): Promise<ApiResult<T>> {
    const {
      method = 'GET',
      body,
      headers = {},
      requestId = generateRequestId(),
    } = options ?? {};

    const startedAt = Date.now();

    try {
      const controller = new AbortController();
      const timeoutHandle = setTimeout(() => controller.abort(), this.timeoutMs);

      try {
        const accessToken = this.getAccessToken();
        const response = await fetch(`${this.baseUrl}${path}`, {
          method,
          headers: {
            'Content-Type': 'application/json',
            'X-Request-Id': requestId,
            ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
            ...headers,
          },
          body: body ? JSON.stringify(body) : undefined,
          signal: controller.signal,
        });

        clearTimeout(timeoutHandle);
        const durationMs = Date.now() - startedAt;

        let payload: BaseResponse<T>;
        try {
          payload = await response.json();
        } catch {
          payload = {
            success: false,
            error: {
              code: 'invalid_json',
              message: 'Invalid JSON response from server',
            },
          };
        }

        const result: ApiResult<T> = {
          ...payload,
          meta: {
            requestId,
            durationMs,
            status: response.status,
          },
        };

        // Handle 401 Unauthorized
        if (response.status === 401) {
          this.onUnauthorized();
        }

        this.logger.info('api_request_completed', {
          path,
          method,
          status: response.status,
          requestId,
          durationMs,
          success: payload.success,
        });

        return result;
      } finally {
        clearTimeout(timeoutHandle);
      }
    } catch (error) {
      const durationMs = Date.now() - startedAt;

      // Check if it's an AbortError (timeout)
      if (error instanceof DOMException && error.name === 'AbortError') {
        this.logger.warn('api_request_timeout', {
          path,
          method,
          requestId,
          durationMs,
          timeoutMs: this.timeoutMs,
        });

        return {
          success: false,
          error: {
            code: 'timeout',
            message: `Request timeout after ${this.timeoutMs}ms`,
          },
          meta: {
            requestId,
            durationMs,
            status: 0,
          },
        };
      }

      // Network error
      this.logger.warn('api_request_error', {
        path,
        method,
        requestId,
        durationMs,
        error: error instanceof Error ? error.message : String(error),
      });

      return {
        success: false,
        error: {
          code: 'network_error',
          message: 'Failed to contact server',
        },
        meta: {
          requestId,
          durationMs,
          status: 0,
        },
      };
    }
  }

  /**
   * GET request
   */
  async get<T = unknown>(
    path: string,
    options?: Omit<Parameters<typeof this.request>[1], 'method'>
  ): Promise<ApiResult<T>> {
    return this.request<T>(path, { ...options, method: 'GET' });
  }

  /**
   * POST request
   */
  async post<T = unknown>(
    path: string,
    body?: Record<string, unknown>,
    options?: Omit<Parameters<typeof this.request>[1], 'method' | 'body'>
  ): Promise<ApiResult<T>> {
    return this.request<T>(path, { ...options, method: 'POST', body });
  }

  /**
   * PUT request
   */
  async put<T = unknown>(
    path: string,
    body?: Record<string, unknown>,
    options?: Omit<Parameters<typeof this.request>[1], 'method' | 'body'>
  ): Promise<ApiResult<T>> {
    return this.request<T>(path, { ...options, method: 'PUT', body });
  }

  /**
   * DELETE request
   */
  async delete<T = unknown>(
    path: string,
    options?: Omit<Parameters<typeof this.request>[1], 'method'>
  ): Promise<ApiResult<T>> {
    return this.request<T>(path, { ...options, method: 'DELETE' });
  }
}

/**
 * Create API client instance with sensible defaults
 */
export function createApiClient(
  baseUrl: string,
  getAccessToken?: () => string | null,
  onUnauthorized?: () => void
): ApiClient {
  return new ApiClient({
    baseUrl,
    timeoutMs: 8000,
    getAccessToken,
    onUnauthorized,
  });
}

/**
 * Get API base URL from environment
 */
export function getApiBaseUrl(): string {
  if (typeof window === 'undefined') {
    // Server-side
    return process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
  }
  // Client-side
  return process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
}
