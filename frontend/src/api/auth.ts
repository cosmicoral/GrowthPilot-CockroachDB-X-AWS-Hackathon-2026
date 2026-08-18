import {
  apiRequest,
  clearSessionToken,
  setSessionToken,
  USES_CROSS_ORIGIN_API,
} from "./client"

interface SessionResponse {
  company_id: string
  session_token?: string
}

function rememberBearerSession(response: SessionResponse) {
  if (response.session_token) setSessionToken(response.session_token)
  return response
}

export interface CompanyProfile {
  id: string
  name: string
  email: string
  website: string | null
  industry: string | null
  description: string | null
}

export interface SignupInput {
  name: string
  email: string
  password: string
  website?: string
  industry?: string
  description?: string
}

export interface OnboardingInput {
  website?: string
  industry?: string
  description?: string
  ideal_customer: string
  three_month_goal: string
  previous_attempts: string
  current_channels: string
}

export async function login(input: { email: string; password: string }) {
  const response = await apiRequest<SessionResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({
      ...input,
      use_bearer_token: USES_CROSS_ORIGIN_API,
    }),
  })
  return rememberBearerSession(response)
}

export async function signup(input: SignupInput) {
  const response = await apiRequest<SessionResponse>("/api/auth/signup", {
    method: "POST",
    body: JSON.stringify({
      ...input,
      use_bearer_token: USES_CROSS_ORIGIN_API,
    }),
  })
  return rememberBearerSession(response)
}

export async function logout() {
  try {
    return await apiRequest<null>("/api/auth/logout", { method: "POST" })
  } finally {
    clearSessionToken()
  }
}

export function getCurrentCompany() {
  return apiRequest<CompanyProfile>("/api/company/me")
}

export function saveOnboarding(input: OnboardingInput) {
  return apiRequest<CompanyProfile>("/api/company/onboarding", {
    method: "POST",
    body: JSON.stringify(input),
  })
}
