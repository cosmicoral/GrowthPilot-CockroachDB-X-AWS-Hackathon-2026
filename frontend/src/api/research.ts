import type { MemoryHit } from "./chat"
import { apiRequest } from "./client"

export type ResearchCategory = "competitors" | "trends" | "pain_points" | "general"

export interface ResearchChunk {
  content: string
  category: ResearchCategory
  importance: number
  metadata: {
    category?: ResearchCategory
    timestamp?: string
    content_origin?: "llm_generated" | "user_input"
    verified?: boolean
    confidence?: string
  }
}

export interface ResearchRunResponse {
  agent_name: string
  success: boolean
  output: {
    company_name?: string
    industry?: string
    raw_research?: string
    structured_chunks?: ResearchChunk[]
    memories_created?: number
    memories_deduplicated?: number
  }
  metadata: Record<string, unknown>
}

export function getResearchMemories(limit = 20) {
  return apiRequest<MemoryHit[]>(`/api/research/memories?limit=${limit}`)
}

export function runMarketResearch(customResearchText?: string) {
  return apiRequest<ResearchRunResponse>("/api/research/run", {
    method: "POST",
    body: JSON.stringify({
      trigger: "manual",
      custom_research_text: customResearchText?.trim() || null,
    }),
  })
}
