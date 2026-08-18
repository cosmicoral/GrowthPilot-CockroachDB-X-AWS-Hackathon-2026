const configuredApiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim()

export const API_BASE_URL = configuredApiBaseUrl
  ? configuredApiBaseUrl.replace(/\/$/, "")
  : ""

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

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      credentials: "include",
      cache: "no-store",
      headers: {
        ...(init.body ? { "Content-Type": "application/json" } : {}),
        ...init.headers,
      },
    })
  } catch {
    throw new ApiError(
      "We could not reach GrowthPilot. Check your connection and try again.",
      0,
    )
  }

  const contentType = response.headers.get("content-type") || ""
  const payload = contentType.includes("application/json")
    ? await response.json()
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
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      credentials: "include",
      cache: "no-store",
      headers: { "Content-Type": "application/json" },
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
