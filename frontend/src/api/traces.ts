import { apiRequest } from "./client"

export interface AgentTraceMemory {
  id?: string | null
  similarity?: number | null
  memory_type?: string | null
  importance?: number | null
  content_preview?: string
  summary?: string
}

export interface AgentTrace {
  id: string
  company_id: string
  agent_name: string
  start_time: string
  duration_ms: number
  input: Record<string, unknown>
  output: unknown
  memories_retrieved: AgentTraceMemory[]
  success: boolean
  error: string | null
  metadata: Record<string, unknown>
  created_at: string
}

export function getAgentTraces(limit = 50, agentName?: string) {
  const params = new URLSearchParams({ limit: String(limit) })
  if (agentName) params.set("agent_name", agentName)
  return apiRequest<AgentTrace[]>(`/api/traces?${params.toString()}`)
}
