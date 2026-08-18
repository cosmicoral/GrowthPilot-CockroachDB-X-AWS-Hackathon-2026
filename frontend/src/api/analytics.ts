import type { MemoryHit } from "./chat"
import { apiRequest } from "./client"

export interface GroupPerformance {
  group_name: string
  post_count: number
  total_likes: number
  total_comments: number
  total_clicks: number
  total_engagement: number
  average_engagement_per_post: number
}

export interface AnalyticsReflectionOutput {
  group_by: "theme" | "icp" | "messaging_angle"
  post_count: number
  groups: GroupPerformance[]
  best_group: string
  analyzed_memory_ids: string[]
  reflection: string
  reflection_memory_id: string | null
}

export function getLatestAnalyticsReflection() {
  return apiRequest<MemoryHit | null>("/api/analytics/latest")
}

export function runAnalyticsReflection(groupBy: AnalyticsReflectionOutput["group_by"] = "theme") {
  return apiRequest<AnalyticsReflectionOutput>("/api/analytics/reflection", {
    method: "POST",
    body: JSON.stringify({ group_by: groupBy }),
  })
}
