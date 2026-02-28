export function createSourcesService(apiClient) {
  return {
    health: () => apiClient.request("/health"),
    upload: (payload) => apiClient.request("/upload", { method: "POST", body: payload }),
    downloadFromUrl: (payload) => apiClient.request("/download-from-url", { method: "POST", body: payload }),
    extract: (payload) => apiClient.request("/extract", { method: "POST", body: payload }),
    listSources: () => apiClient.request("/sources"),
    getSource: (fileId) => apiClient.request(`/source/${fileId}`),
    videoToText: (payload) => apiClient.request("/video-to-text", { method: "POST", body: payload }),
    aiAssist: (payload) => apiClient.request("/ai-assist", { method: "POST", body: payload }),
  };
}
