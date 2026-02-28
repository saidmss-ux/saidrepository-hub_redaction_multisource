import test from "node:test";
import assert from "node:assert/strict";

import { ApiClient } from "../src/api/apiClient.js";
import { resolveApiBaseByEnv } from "../src/api/env.js";
import { runRequest } from "../src/state/createRequestState.js";

function responseOf(payload, status = 200, headers = {}) {
  return {
    status,
    headers: {
      get(name) {
        return headers[name.toLowerCase()] || null;
      },
    },
    async json() {
      return payload;
    },
  };
}

test("ApiClient returns success payload and propagates x-request-id", async () => {
  const client = new ApiClient({
    baseUrl: "/api/v1",
    fetchImpl: async (_url, options) => {
      assert.ok(options.headers["x-request-id"]);
      return responseOf(
        { success: true, data: { status: "ok" }, error: null },
        200,
        { "x-request-id": "srv-123" },
      );
    },
    logger: { info() {}, warn() {} },
  });

  const result = await client.request("/health");
  assert.equal(result.success, true);
  assert.equal(result.data.status, "ok");
  assert.equal(result.meta.requestId, "srv-123");
});

test("ApiClient injects bearer token and handles 401 callback", async () => {
  let unauthorizedCalled = false;
  const client = new ApiClient({
    getAccessToken: () => "abc123",
    onUnauthorized: () => {
      unauthorizedCalled = true;
    },
    fetchImpl: async (_url, options) => {
      assert.equal(options.headers.authorization, "Bearer abc123");
      return responseOf(
        { success: false, data: null, error: { code: "auth_missing", message: "auth", details: {} } },
        401,
      );
    },
    logger: { info() {}, warn() {} },
  });

  const result = await client.request("/projects");
  assert.equal(result.success, false);
  assert.equal(result.meta.status, 401);
  assert.equal(unauthorizedCalled, true);
});

test("ApiClient handles contract errors and retry over_capacity", async () => {
  let calls = 0;
  const client = new ApiClient({
    retryCount: 1,
    retryDelayMs: 1,
    fetchImpl: async () => {
      calls += 1;
      if (calls === 1) {
        return responseOf({
          success: false,
          data: null,
          error: { code: "over_capacity", message: "busy", details: {} },
        }, 503);
      }
      return responseOf({ success: true, data: { retry: true }, error: null }, 200);
    },
    logger: { info() {}, warn() {} },
  });

  const result = await client.request("/sources");
  assert.equal(calls, 2);
  assert.equal(result.success, true);
  assert.equal(result.data.retry, true);
});

test("runRequest maps over_capacity status for UI layer", async () => {
  const { finalState } = await runRequest(async () => ({
    success: false,
    data: null,
    error: { code: "over_capacity", message: "busy", details: {} },
    meta: { requestId: "req1", durationMs: 10, status: 503 },
  }));

  assert.equal(finalState.status, "over_capacity");
  assert.equal(finalState.requestId, "req1");
});

test("resolveApiBaseByEnv returns environment specific base", () => {
  assert.equal(resolveApiBaseByEnv("local"), "/api/v1");
  assert.equal(resolveApiBaseByEnv("staging"), "/api/v1");
  assert.equal(resolveApiBaseByEnv("production"), "/api/v1");
});
