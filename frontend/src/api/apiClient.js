import { messageForCode } from "./errorMessages.js";
import { resolveApiBaseByEnv } from "./env.js";

function defaultRequestId() {
  if (globalThis.crypto && typeof globalThis.crypto.randomUUID === "function") {
    return globalThis.crypto.randomUUID();
  }
  return `req_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

export class ApiClient {
  constructor({
    baseUrl = resolveApiBaseByEnv(),
    timeoutMs = 8000,
    retryCount = 1,
    retryDelayMs = 200,
    fetchImpl = fetch,
    logger = console,
    getAccessToken = () => null,
    onUnauthorized = () => {},
  } = {}) {
    this.baseUrl = baseUrl;
    this.timeoutMs = timeoutMs;
    this.retryCount = retryCount;
    this.retryDelayMs = retryDelayMs;
    this.fetchImpl = fetchImpl;
    this.logger = logger;
    this.getAccessToken = getAccessToken;
    this.onUnauthorized = onUnauthorized;
  }

  async request(path, { method = "GET", body, headers = {}, requestId } = {}) {
    const finalRequestId = requestId || defaultRequestId();
    const startedAt = Date.now();

    let attempt = 0;
    while (attempt <= this.retryCount) {
      try {
        const result = await this.#singleRequest(path, {
          method,
          body,
          headers,
          requestId: finalRequestId,
          startedAt,
        });

        if (result.meta?.status === 401) {
          this.onUnauthorized(result);
        }

        if (result.error?.code === "over_capacity" && attempt < this.retryCount) {
          await this.#sleep(this.retryDelayMs * (attempt + 1));
          attempt += 1;
          continue;
        }
        return result;
      } catch (error) {
        if (attempt < this.retryCount) {
          await this.#sleep(this.retryDelayMs * (attempt + 1));
          attempt += 1;
          continue;
        }

        const durationMs = Date.now() - startedAt;
        this.logger.warn("api_request_exception", {
          path,
          method,
          requestId: finalRequestId,
          durationMs,
          error: String(error),
        });

        return {
          success: false,
          data: null,
          error: {
            code: "network_exception",
            message: "Impossible de contacter le service.",
            details: {},
          },
          meta: {
            requestId: finalRequestId,
            durationMs,
            status: 0,
          },
        };
      }
    }

    return {
      success: false,
      data: null,
      error: { code: "unknown_error", message: messageForCode("unknown_error"), details: {} },
      meta: { requestId: finalRequestId, durationMs: Date.now() - startedAt, status: 0 },
    };
  }

  async #singleRequest(path, { method, body, headers, requestId, startedAt }) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.timeoutMs);

    try {
      const accessToken = this.getAccessToken();
      const response = await this.fetchImpl(`${this.baseUrl}${path}`, {
        method,
        headers: {
          "content-type": "application/json",
          "x-request-id": requestId,
          ...(accessToken ? { authorization: `Bearer ${accessToken}` } : {}),
          ...headers,
        },
        body: body == null ? undefined : JSON.stringify(body),
        signal: controller.signal,
      });

      const durationMs = Date.now() - startedAt;
      const responseRequestId = response.headers?.get?.("x-request-id") || requestId;

      let payload;
      try {
        payload = await response.json();
      } catch {
        payload = {
          success: false,
          data: null,
          error: { code: "invalid_json", message: "Réponse serveur invalide.", details: {} },
        };
      }

      const normalized = this.#normalizePayload(payload);
      this.logger.info("api_request_completed", {
        path,
        method,
        status: response.status,
        requestId: responseRequestId,
        durationMs,
        errorCode: normalized.error?.code || null,
      });

      return {
        ...normalized,
        meta: {
          requestId: responseRequestId,
          durationMs,
          status: response.status,
        },
      };
    } finally {
      clearTimeout(timeout);
    }
  }

  #normalizePayload(payload) {
    const success = Boolean(payload?.success);
    const data = success ? payload?.data ?? null : null;
    const code = payload?.error?.code || (success ? null : "unknown_error");

    if (success) {
      return { success: true, data, error: null };
    }

    return {
      success: false,
      data: null,
      error: {
        code,
        message: payload?.error?.message || messageForCode(code),
        details: payload?.error?.details || {},
      },
    };
  }

  #sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}
