export function resolveApiBaseByEnv(env = process.env.APP_ENV || "local") {
  const normalized = String(env).toLowerCase();
  if (normalized === "production") {
    return process.env.API_BASE_PRODUCTION || "/api/v1";
  }
  if (normalized === "staging") {
    return process.env.API_BASE_STAGING || "/api/v1";
  }
  return process.env.API_BASE_LOCAL || "/api/v1";
}
