import { apiRequest } from "./client"

export interface GrowthGraphInsight {
  theme: string
  summary: string
  matched_founders: number
  cohort_size: number
  prevalence: number | null
  average_similarity: number | null
}

export interface GrowthGraphResponse {
  query: string
  cohort_size: number
  generated_at?: string
  insight?: string
  insights?: GrowthGraphInsight[]
}

/**
 * T36 frontend contract. The response deliberately has no company IDs,
 * memory IDs, founder names, or raw memory content.
 */
export function getGrowthGraphInsights(query: string) {
  return apiRequest<GrowthGraphResponse>("/api/growthgraph/insights", {
    method: "POST",
    body: JSON.stringify({ query: query.trim() }),
  })
}
