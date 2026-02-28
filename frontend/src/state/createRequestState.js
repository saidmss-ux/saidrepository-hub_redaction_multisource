export const initialRequestState = {
  status: "idle",
  data: null,
  error: null,
  requestId: null,
  durationMs: 0,
};

export async function runRequest(requestFn) {
  const loadingState = {
    ...initialRequestState,
    status: "loading",
  };

  const result = await requestFn();

  if (result.success) {
    return {
      loadingState,
      finalState: {
        status: "success",
        data: result.data,
        error: null,
        requestId: result.meta?.requestId || null,
        durationMs: result.meta?.durationMs || 0,
      },
    };
  }

  const status = result.error?.code === "over_capacity" ? "over_capacity" : "error";
  return {
    loadingState,
    finalState: {
      status,
      data: null,
      error: result.error,
      requestId: result.meta?.requestId || null,
      durationMs: result.meta?.durationMs || 0,
    },
  };
}
