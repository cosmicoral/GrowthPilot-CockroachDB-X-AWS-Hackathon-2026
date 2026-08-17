import { useEffect, useRef, useState } from "react"
import Logo from "@/components/Logo"
import { streamChat, type MemoryHit, type PlannerMetadata } from "@/api/chat"

interface Message {
  id: string
  role: "ai" | "user"
  text: string
  memories?: MemoryHit[]
  planner?: PlannerMetadata
  error?: string
}

const QUICK_SUGGESTIONS = [
  "How should I refine my ICP?",
  "What have we learned from previous campaigns?",
  "Write me a cold email opener",
  "What should I post about this week?",
]

function relativeTime(value: string) {
  const timestamp = new Date(value).getTime()
  const seconds = Math.max(0, Math.floor((Date.now() - timestamp) / 1000))
  if (seconds < 60) return "just now"
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
  return `${Math.floor(seconds / 86400)}d ago`
}

function MemoryInspector({ memories }: { memories: MemoryHit[] }) {
  const [open, setOpen] = useState(false)

  return (
    <div className="memory-inspector">
      <button type="button" className="memory-toggle" onClick={() => setOpen((current) => !current)}>
        🧠 Answered using {memories.length} {memories.length === 1 ? "memory" : "memories"} from your history
        <span>{open ? "−" : "+"}</span>
      </button>
      {open && <div className="memory-list">
        {memories.map((memory) => {
          const similarity = memory.similarity == null ? null : Math.max(0, Math.min(1, memory.similarity))
          return <article className="memory-hit" key={memory.id}>
            <div className="memory-hit-header">
              <span className={`memory-type memory-type-${memory.memory_type}`}>{memory.memory_type}</span>
              <span>{relativeTime(memory.created_at)}</span>
            </div>
            <p>{memory.content}</p>
            <div className="memory-metrics">
              <span>Similarity {similarity == null ? "n/a" : `${Math.round(similarity * 100)}%`}</span>
              <span>Importance {Math.round(memory.importance * 100)}%</span>
            </div>
            {similarity != null && <div className="memory-score"><span style={{ width: `${similarity * 100}%` }} /></div>}
          </article>
        })}
      </div>}
    </div>
  )
}

export default function AIPartner() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "ai",
      text: "Hi! I’m your GrowthPilot AI Partner. Ask about your market, positioning, content, or what we learned from earlier work.",
    },
  ])
  const [input, setInput] = useState("")
  const [isSending, setIsSending] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  async function sendMessage(rawText: string) {
    const text = rawText.trim()
    if (!text || isSending) return

    const responseId = crypto.randomUUID()
    setMessages((current) => [
      ...current,
      { id: crypto.randomUUID(), role: "user", text },
      { id: responseId, role: "ai", text: "" },
    ])
    setInput("")
    setIsSending(true)

    try {
      await streamChat(text, {
        onMemories(memories) {
          setMessages((current) => current.map((message) => message.id === responseId ? { ...message, memories } : message))
        },
        onToken(token) {
          setMessages((current) => current.map((message) => message.id === responseId ? { ...message, text: message.text + token } : message))
        },
        onDone(planner) {
          setMessages((current) => current.map((message) => message.id === responseId ? { ...message, planner } : message))
        },
      })
    } catch (error) {
      setMessages((current) => current.map((message) => message.id === responseId
        ? { ...message, error: error instanceof Error ? error.message : "The response stopped unexpectedly." }
        : message))
    } finally {
      setIsSending(false)
    }
  }

  function submit(event: React.FormEvent) {
    event.preventDefault()
    void sendMessage(input)
  }

  return (
    <section className="ai-partner" aria-labelledby="ai-partner-heading">
      <header className="dashboard-page-heading">
        <div>
          <p className="dashboard-kicker">MEMORY-AWARE CHAT</p>
          <h1 id="ai-partner-heading">AI Partner</h1>
        </div>
        <span className="connection-badge">● Connected to GrowthPilot API</span>
      </header>

      <div className="chat-window" aria-live="polite">
        {messages.map((message) => <div className={`chat-row chat-row-${message.role}`} key={message.id}>
          <div className="chat-avatar">{message.role === "ai" ? <Logo size={22} /> : "You"}</div>
          <div className="chat-message">
            {message.text ? <p>{message.text}</p> : <p className="typing-indicator">GrowthPilot is thinking…</p>}
            {message.error && <div className="form-error" role="alert">{message.error}</div>}
            {message.role === "ai" && message.planner && <div className="planner-summary">
              <span>{message.planner.decision.execution}</span>
              <span>{message.planner.decision.intents.join(" + ")}</span>
              {message.planner.partial && <strong>Partial result · {message.planner.failed_agents.join(", ")} unavailable</strong>}
            </div>}
            {message.role === "ai" && message.memories && message.memories.length > 0 && <MemoryInspector memories={message.memories} />}
          </div>
        </div>)}
        <div ref={bottomRef} />
      </div>

      <div className="chat-suggestions">
        {QUICK_SUGGESTIONS.map((suggestion) => <button disabled={isSending} key={suggestion} onClick={() => void sendMessage(suggestion)}>{suggestion}</button>)}
      </div>

      <form className="chat-composer" onSubmit={submit}>
        <label className="sr-only" htmlFor="chat-message">Message GrowthPilot</label>
        <textarea id="chat-message" value={input} disabled={isSending} onChange={(event) => setInput(event.target.value)} onKeyDown={(event) => {
          if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault()
            void sendMessage(input)
          }
        }} placeholder="Ask GrowthPilot about your strategy, market, or memory…" rows={2} />
        <button type="submit" disabled={isSending || !input.trim()}>{isSending ? "Thinking…" : "Send →"}</button>
      </form>
    </section>
  )
}
