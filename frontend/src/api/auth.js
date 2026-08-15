const configuredApiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim();
const API_BASE_URL = configuredApiBaseUrl
  ? configuredApiBaseUrl.replace(/\/$/, "")
  : "";

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function errorMessage(payload, fallback) {
  if (typeof payload?.detail === "string") {
    return payload.detail;
  }

  if (Array.isArray(payload?.detail) && payload.detail.length > 0) {
    return payload.detail[0]?.msg?.replace(/^Value error,\s*/i, "") || fallback;
  }

  return fallback;
}

async function apiRequest(path, options = {}) {
  let response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      credentials: "include",
      cache: "no-store",
      headers: {
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...options.headers,
      },
    });
  } catch {
    throw new ApiError(
      "We could not reach GrowthPilot. Check your connection and try again.",
      0,
    );
  }

  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : null;

  if (!response.ok) {
    throw new ApiError(
      errorMessage(payload, "Something went wrong. Please try again."),
      response.status,
    );
  }

  return payload;
}

export function login(credentials) {
  return apiRequest("/api/auth/login", {
    method: "POST",
    body: JSON.stringify(credentials),
  });
}

export function signup(account) {
  return apiRequest("/api/auth/signup", {
    method: "POST",
    body: JSON.stringify(account),
  });
}

export function logout() {
  return apiRequest("/api/auth/logout", { method: "POST" });
}

export function getCurrentCompany() {
  return apiRequest("/api/company/me");
}
