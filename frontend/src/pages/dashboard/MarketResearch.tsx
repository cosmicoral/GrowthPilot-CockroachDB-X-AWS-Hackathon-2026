import { useEffect, useMemo, useState } from "react"
import type { MemoryHit } from "@/api/chat"
import {
  getResearchMemories,
  runMarketResearch,
  type ResearchCategory,
  type ResearchChunk,
} from "@/api/research"

interface ResearchItem {
  id: string
  content: string
  category: ResearchCategory
  timestamp?: string
  verified: boolean
}

const SECTIONS: Array<{ category: ResearchCategory; title: string; description: string }> = [
  { category: "competitors", title: "Competitor landscape", description: "Positioning, strengths, weaknesses, and differentiation signals." },
  { category: "trends", title: "Industry trends", description: "Tailwinds, shifts, and opportunities relevant to your market." },
  { category: "pain_points", title: "Customer pain points", description: "Repeated friction, unmet needs, and buying obstacles." },
  { category: "general", title: "Additional findings", description: "Useful context that does not fit the focused categories above." },
]

function categoryFromMetadata(metadata: Record<string, unknown>): ResearchCategory {
  const category = metadata.category
  return category === "competitors" || category === "trends" || category === "pain_points"
    ? category
    : "general"
}

function itemFromMemory(memory: MemoryHit): ResearchItem {
  return {
    id: memory.id,
    content: memory.content,
    category: categoryFromMetadata(memory.metadata),
    timestamp: typeof memory.metadata.timestamp === "string" ? memory.metadata.timestamp : memory.created_at,
    verified: memory.metadata.verified === true,
  }
}

function itemFromChunk(chunk: ResearchChunk, index: number): ResearchItem {
  return {
    id: `research-${index}`,
    content: chunk.content,
    category: chunk.category || chunk.metadata.category || "general",
    timestamp: chunk.metadata.timestamp,
    verified: chunk.metadata.verified === true,
  }
}

function formatTimestamp(value?: string) {
  if (!value) return "Saved research"
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime())
    ? "Saved research"
    : new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(parsed)
}

export default function MarketResearch() {
  const [items, setItems] = useState<ResearchItem[]>([])
  const [customText, setCustomText] = useState("")
  const [isLoading, setIsLoading] = useState(true)
  const [isRunning, setIsRunning] = useState(false)
  const [error, setError] = useState("")
  const [runSummary, setRunSummary] = useState("")

  async function loadSavedResearch() {
    setError("")
    try {
      const memories = await getResearchMemories()
      setItems(memories.map(itemFromMemory))
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Saved research could not be loaded.")
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    void loadSavedResearch()
  }, [])

  async function handleRunResearch() {
    if (isRunning) return
    setError("")
    setRunSummary("")
    setIsRunning(true)

    try {
      const response = await runMarketResearch(customText)
      const chunks = response.output.structured_chunks || []
      setItems(chunks.map(itemFromChunk))
      setRunSummary(
        `${response.output.memories_created ?? chunks.length} new research memories saved` +
        (response.output.memories_deduplicated ? ` · ${response.output.memories_deduplicated} reused` : ""),
      )
      setCustomText("")
    } catch (runError) {
      setError(runError instanceof Error ? runError.message : "Market research could not be completed.")
    } finally {
      setIsRunning(false)
    }
  }

  const groupedItems = useMemo(() => Object.fromEntries(
    SECTIONS.map(({ category }) => [category, items.filter((item) => item.category === category)]),
  ) as Record<ResearchCategory, ResearchItem[]>, [items])

  return (
    <section className="research-page" aria-labelledby="market-research-heading">
      <header className="dashboard-page-heading">
        <div>
          <p className="dashboard-kicker">LIVE AGENT WORKSPACE</p>
          <h1 id="market-research-heading">Market Research</h1>
        </div>
        <span className="connection-badge">● Connected to Market Research Agent</span>
      </header>

      <div className="research-run-card">
        <div>
          <h2>Refresh your market context</h2>
          <p>Run the agent from your saved company profile, or paste trusted source text for it to structure and remember.</p>
        </div>
        <label htmlFor="research-source">Optional source text</label>
        <textarea
          id="research-source"
          value={customText}
          onChange={(event) => setCustomText(event.target.value)}
          placeholder="Paste interview notes, competitor research, or another source. Leave empty to use Bedrock research."
          rows={4}
          disabled={isRunning}
        />
        <div className="research-actions">
          <span>AI-generated findings remain marked unverified until you confirm them.</span>
          <button type="button" onClick={() => void handleRunResearch()} disabled={isRunning}>
            {isRunning ? "Researching…" : "Run market research →"}
          </button>
        </div>
      </div>

      {error && <div className="form-error" role="alert">{error}</div>}
      {runSummary && <p className="research-success" role="status">✓ {runSummary}</p>}

      {isLoading ? (
        <div className="research-empty" aria-live="polite">Loading saved market research…</div>
      ) : items.length === 0 ? (
        <div className="research-empty">
          <strong>No research memories yet.</strong>
          <span>Run the Market Research Agent to create the first evidence-backed workspace.</span>
        </div>
      ) : (
        <div className="research-section-grid">
          {SECTIONS.map((section) => {
            const sectionItems = groupedItems[section.category]
            if (sectionItems.length === 0) return null
            return (
              <article className="research-section" key={section.category}>
                <header>
                  <div>
                    <h2>{section.title}</h2>
                    <p>{section.description}</p>
                  </div>
                  <span>{sectionItems.length}</span>
                </header>
                <div className="research-finding-list">
                  {sectionItems.map((item) => (
                    <div className="research-finding" key={item.id}>
                      <p>{item.content}</p>
                      <footer>
                        <span>{formatTimestamp(item.timestamp)}</span>
                        <span className={item.verified ? "research-verified" : "research-unverified"}>
                          {item.verified ? "Verified" : "Unverified AI finding"}
                        </span>
                      </footer>
                    </div>
                  ))}
                </div>
              </article>
            )
          })}
        </div>
      )}
    </section>
  )
}
