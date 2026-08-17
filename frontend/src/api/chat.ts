import { apiRequest, apiStream } from "./client"

export type MemoryType =
  | "episodic"
  | "semantic"
  | "user"
  | "task"
  | "reflection"

export interface MemoryHit {
  id: string
  company_id: string
  content: string
  memory_type: MemoryType
  metadata: Record<string, unknown>
  importance: number
  similarity: number | null
  created_at: string
}

export interface PlannerMetadata {
  decision: {
    intents: string[]
    execution: "single" | "sequential" | "parallel"
    reason: string
  }
  partial: boolean
  failed_agents: string[]
}

type StreamEvent =
  | { type: "memories"; memories: MemoryHit[] }
  | { type: "token"; text: string }
  | { type: "done"; metadata: PlannerMetadata }
  | { type: "error"; detail: string }

interface StreamHandlers {
  onMemories: (memories: MemoryHit[]) => void
  onToken: (text: string) => void
  onDone?: (metadata: PlannerMetadata) => void
}

function parseEvent(block: string): StreamEvent | null {
  const data = block
    .split("\n")
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.slice(5).trimStart())
    .join("\n")

  if (!data) return null
  return JSON.parse(data) as StreamEvent
}

export async function streamChat(message: string, handlers: StreamHandlers) {
  const stream = await apiStream("/api/chat/stream", { message })
  const reader = stream.getReader()
  const decoder = new TextDecoder()
  let buffer = ""

  while (true) {
    const { value, done } = await reader.read()
    buffer += decoder.decode(value, { stream: !done })

    const blocks = buffer.split(/\r?\n\r?\n/)
    buffer = blocks.pop() || ""

    for (const block of blocks) {
      const event = parseEvent(block)
      if (!event) continue
      if (event.type === "memories") handlers.onMemories(event.memories)
      if (event.type === "token") handlers.onToken(event.text)
      if (event.type === "error") throw new Error(event.detail)
      if (event.type === "done") {
        handlers.onDone?.(event.metadata)
        return
      }
    }

    if (done) break
  }

  if (buffer.trim()) {
    const event = parseEvent(buffer)
    if (event?.type === "error") throw new Error(event.detail)
    if (event?.type === "token") handlers.onToken(event.text)
  }
}

export function generateContent(prompt: string) {
  return apiRequest<{ content: string; memories: MemoryHit[] }>("/api/chat/generate-content", {
    method: "POST",
    body: JSON.stringify({ prompt }),
  })
}

export function searchMemories(query: string, k = 8) {
  return apiRequest<MemoryHit[]>("/api/memory/search", {
    method: "POST",
    body: JSON.stringify({ query, k }),
  })
}
