import { apiRequest } from "./client"

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

export function login(input: { email: string; password: string }) {
  return apiRequest<{ company_id: string }>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify(input),
  })
}

export function signup(input: SignupInput) {
  return apiRequest<{ company_id: string }>("/api/auth/signup", {
    method: "POST",
    body: JSON.stringify(input),
  })
}

export function logout() {
  return apiRequest<null>("/api/auth/logout", { method: "POST" })
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
