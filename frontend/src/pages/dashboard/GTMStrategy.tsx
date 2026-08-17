import { useState } from "react"
import { streamChat, type MemoryHit, type PlannerMetadata } from "@/api/chat"
import MemoryInspector from "@/components/MemoryInspector"

const DEFAULT_PROMPT = "Create a concise go-to-market strategy from our saved company profile, market research, goals, and previous attempts. Include positioning, ICP, ranked channels, and the next three experiments. Clearly say when the available memory is insufficient."

export default function GTMStrategy() {
  const [prompt, setPrompt] = useState(DEFAULT_PROMPT)
  const [strategy, setStrategy] = useState("")
  const [memories, setMemories] = useState<MemoryHit[]>([])
  const [planner, setPlanner] = useState<PlannerMetadata | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState("")

  async function generateStrategy() {
    const request = prompt.trim()
    if (!request || isGenerating) return
    setStrategy("")
    setMemories([])
    setPlanner(null)
    setError("")
    setIsGenerating(true)
    try {
      await streamChat(request, {
        onMemories: setMemories,
        onToken: (token) => setStrategy((current) => current + token),
        onDone: setPlanner,
      })
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "GTM strategy generation failed.")
    } finally {
      setIsGenerating(false)
    }
  }

  return <section className="gtm-live-page" aria-labelledby="gtm-heading">
    <header className="dashboard-page-heading">
      <div>
        <p className="dashboard-kicker">MEMORY-GROUNDED PLANNER OUTPUT</p>
        <h1 id="gtm-heading">GTM Strategy</h1>
      </div>
      {planner && <span className="connection-badge">Planner · {planner.decision.execution}</span>}
    </header>

    <div className="gtm-generator">
      <label htmlFor="gtm-request">Strategy request</label>
      <textarea id="gtm-request" value={prompt} onChange={(event) => setPrompt(event.target.value)} rows={5} disabled={isGenerating} />
      <div>
        <span>This view only shows live Planner output grounded in saved company memories.</span>
        <button type="button" onClick={() => void generateStrategy()} disabled={isGenerating || !prompt.trim()}>
          {isGenerating ? "Building strategy…" : "Generate live strategy →"}
        </button>
      </div>
    </div>

    {error && <div className="form-error" role="alert">{error}</div>}

    {!strategy && !isGenerating && !error ? <div className="research-empty">
      <strong>No generated strategy yet.</strong>
      <span>Run the Planner to replace the previous static personas, channels, and timeline with company-specific output.</span>
    </div> : <article className="gtm-output" aria-live="polite">
      <header>
        <div><p className="dashboard-kicker">REAL AGENT RESPONSE</p><h2>Generated GTM strategy</h2></div>
        {planner && <div className="planner-summary">
          <span>{planner.decision.intents.join(" + ")}</span>
          <span>{planner.decision.execution}</span>
          {planner.partial && <strong>Partial result · {planner.failed_agents.join(", ")}</strong>}
        </div>}
      </header>
      <div className="gtm-output-text">{strategy || "GrowthPilot is thinking…"}</div>
      {memories.length > 0 && <MemoryInspector memories={memories} label={`Strategy grounded in ${memories.length} ${memories.length === 1 ? "memory" : "memories"}`} />}
    </article>}
  </section>
}
