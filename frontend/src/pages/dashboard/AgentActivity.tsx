import { useEffect, useMemo, useState } from "react"
import { getAgentTraces, type AgentTrace } from "@/api/traces"

function formatTime(value: string) {
  const date = new Date(value)
  return Number.isNaN(date.getTime())
    ? value
    : new Intl.DateTimeFormat(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(date)
}

function readableAgentName(value: string) {
  return value.replace(/-/g, " ").replace(/\b\w/g, (letter: string) => letter.toUpperCase())
}

function JsonDetails({ label, value }: { label: string; value: unknown }) {
  return <details className="trace-json-details">
    <summary>{label}</summary>
    <pre>{JSON.stringify(value, null, 2)}</pre>
  </details>
}

export default function AgentActivity() {
  const [allTraces, setAllTraces] = useState<AgentTrace[]>([])
  const [selectedAgent, setSelectedAgent] = useState("")
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState("")

  async function loadTraces() {
    setIsLoading(true)
    setError("")
    try {
      setAllTraces(await getAgentTraces(50))
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Agent activity could not be loaded.")
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    void loadTraces()
  }, [])

  const agentNames = useMemo(
    () => Array.from(new Set(allTraces.map((trace) => trace.agent_name))).sort(),
    [allTraces],
  )
  const traces = selectedAgent
    ? allTraces.filter((trace) => trace.agent_name === selectedAgent)
    : allTraces

  return <section className="trace-page" aria-labelledby="trace-heading">
    <header className="dashboard-page-heading">
      <div>
        <p className="dashboard-kicker">T20 AGENT OBSERVABILITY</p>
        <h1 id="trace-heading">Agent Activity</h1>
      </div>
      <button className="secondary-action" type="button" onClick={() => void loadTraces()} disabled={isLoading}>
        {isLoading ? "Refreshing…" : "Refresh traces"}
      </button>
    </header>

    <div className="trace-toolbar">
      <label htmlFor="trace-agent">Agent</label>
      <select
        id="trace-agent"
        value={selectedAgent}
        onChange={(event) => {
          const value = event.target.value
          setSelectedAgent(value)
        }}
      >
        <option value="">All agents</option>
        {agentNames.map((name) => <option key={name} value={name}>{readableAgentName(name)}</option>)}
      </select>
      <span>{traces.length} recent run{traces.length === 1 ? "" : "s"}</span>
    </div>

    {error && <div className="form-error" role="alert">{error}</div>}
    {isLoading && traces.length === 0 ? (
      <div className="research-empty">Loading agent traces…</div>
    ) : traces.length === 0 ? (
      <div className="research-empty">
        <strong>No agent traces yet.</strong>
        <span>Run Market Research, Analytics, Content, or AI Partner to create the first trace.</span>
      </div>
    ) : (
      <div className="trace-list">
        {traces.map((trace) => <article className="trace-card" key={trace.id}>
          <header>
            <div>
              <span className={`trace-status trace-status-${trace.success ? "success" : "failure"}`}>
                {trace.success ? "Success" : "Failed"}
              </span>
              <h2>{readableAgentName(trace.agent_name)}</h2>
            </div>
            <div className="trace-timing">
              <strong>{Math.round(trace.duration_ms)} ms</strong>
              <span>{formatTime(trace.created_at)}</span>
            </div>
          </header>
          <div className="trace-summary-grid">
            <div><span>Memories retrieved</span><strong>{trace.memories_retrieved.length}</strong></div>
            <div><span>Started</span><strong>{formatTime(trace.start_time)}</strong></div>
          </div>
          {trace.error && <div className="form-error" role="alert">{trace.error}</div>}
          <div className="trace-details-grid">
            <JsonDetails label="Safe input" value={trace.input} />
            <JsonDetails label="Agent output" value={trace.output} />
            <JsonDetails label="Memory provenance" value={trace.memories_retrieved} />
          </div>
        </article>)}
      </div>
    )}
  </section>
}
