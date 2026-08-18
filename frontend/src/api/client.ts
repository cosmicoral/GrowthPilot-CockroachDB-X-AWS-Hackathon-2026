const configuredApiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim()

export const API_BASE_URL = configuredApiBaseUrl
  ? configuredApiBaseUrl.replace(/\/$/, "")
  : ""

export const USES_CROSS_ORIGIN_API = (() => {
  if (!API_BASE_URL || typeof window === "undefined") return false
  return new URL(API_BASE_URL, window.location.origin).origin !== window.location.origin
})()

const SESSION_TOKEN_KEY = "growthpilot_session_token"
let inMemorySessionToken: string | null = null

export function getSessionToken() {
  if (inMemorySessionToken) return inMemorySessionToken
  try {
    return window.sessionStorage.getItem(SESSION_TOKEN_KEY)
  } catch {
    return null
  }
}

export function setSessionToken(token: string) {
  inMemorySessionToken = token
  try {
    window.sessionStorage.setItem(SESSION_TOKEN_KEY, token)
  } catch {
    // The in-memory fallback still supports browsers with disabled storage.
  }
}

export function clearSessionToken() {
  inMemorySessionToken = null
  try {
    window.sessionStorage.removeItem(SESSION_TOKEN_KEY)
  } catch {
    // Nothing else to clear when storage is unavailable.
  }
}

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = "ApiError"
    this.status = status
  }
}

function errorMessage(payload: unknown, fallback: string) {
  if (!payload || typeof payload !== "object" || !("detail" in payload)) {
    return fallback
  }

  const detail = (payload as { detail?: unknown }).detail
  if (typeof detail === "string") return detail
  if (Array.isArray(detail) && detail.length > 0) {
    const message = detail[0]?.msg
    if (typeof message === "string") {
      return message.replace(/^Value error,\s*/i, "")
    }
  }
  return fallback
}

export async function apiRequest<T>(path: string, init: RequestInit = {}) {
  let response: Response
  const sessionToken = getSessionToken()

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      credentials: "include",
      cache: "no-store",
      headers: {
        ...(init.body ? { "Content-Type": "application/json" } : {}),
        ...(sessionToken ? { Authorization: `Bearer ${sessionToken}` } : {}),
        ...init.headers,
      },
    })
  } catch {
    throw new ApiError(
      "We could not reach GrowthPilot. Check your connection and try again.",
      0,
    )
  }

  // 204 responses carry no body, but FastAPI still sends
  // `content-type: application/json`, so a content-type check alone is not
  // enough -- calling .json() on an empty body throws "Unexpected end of
  // JSON input", and that exception propagates out of whatever caller was
  // awaiting it. POST /api/auth/logout returns 204, which is why signing out
  // silently failed: the navigate() after it never ran.
  //
  // Guard on status first, then treat an unparseable body as "no payload"
  // rather than an error. Any endpoint that legitimately returns nothing
  // should not be able to break a caller.
  const contentType = response.headers.get("content-type") || ""
  const hasBody = response.status !== 204 && response.status !== 205
  const payload = hasBody && contentType.includes("application/json")
    ? await response.json().catch(() => null)
    : null

  if (!response.ok) {
    throw new ApiError(
      errorMessage(payload, "Something went wrong. Please try again."),
      response.status,
    )
  }

  return payload as T
}

export async function apiStream(path: string, body: unknown) {
  let response: Response
  const sessionToken = getSessionToken()
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      credentials: "include",
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
        ...(sessionToken ? { Authorization: `Bearer ${sessionToken}` } : {}),
      },
      body: JSON.stringify(body),
    })
  } catch {
    throw new ApiError(
      "We could not reach GrowthPilot. Check your connection and try again.",
      0,
    )
  }

  if (!response.ok) {
    const payload = await response.json().catch(() => null)
    throw new ApiError(
      errorMessage(payload, "The AI request could not be started."),
      response.status,
    )
  }
  if (!response.body) {
    throw new ApiError("The AI stream was not available.", response.status)
  }
  return response.body
}
