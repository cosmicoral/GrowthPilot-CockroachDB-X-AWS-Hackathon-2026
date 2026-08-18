import { useCallback, useEffect, useMemo, useState } from "react"
import type { CSSProperties } from "react"
import { useNavigate, useOutletContext } from "react-router-dom"
import type { CompanyProfile } from "@/api/auth"
import {
  getLatestAnalyticsReflection,
  runAnalyticsReflection,
  type GroupPerformance,
} from "@/api/analytics"
import type { MemoryHit } from "@/api/chat"
import { getResearchMemories } from "@/api/research"
import { getAgentTraces, type AgentTrace } from "@/api/traces"

const card: CSSProperties = {
  background: "rgba(255,255,255,0.93)",
  border: "1.5px solid rgba(255,255,255,0.7)",
  borderRadius: 16,
  padding: 20,
  backdropFilter: "blur(8px)",
}

function formatTime(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  const hours = Math.max(0, Math.round((Date.now() - date.getTime()) / 3_600_000))
  return new Intl.RelativeTimeFormat(undefined, { numeric: "auto" }).format(-hours, "hour")
}

function readable(value: string) {
  return value.replace(/[_-]/g, " ").replace(/\b\w/g, (letter: string) => letter.toUpperCase())
}

function analyticsGroups(memory: MemoryHit | null): GroupPerformance[] {
  const value = memory?.metadata.aggregates
  if (!Array.isArray(value)) return []
  return value.filter((item): item is GroupPerformance => {
    if (!item || typeof item !== "object") return false
    const group = item as Partial<GroupPerformance>
    return typeof group.group_name === "string"
      && typeof group.total_likes === "number"
      && typeof group.total_comments === "number"
      && typeof group.total_clicks === "number"
      && typeof group.average_engagement_per_post === "number"
  })
}

export default function DashboardHome() {
  const navigate = useNavigate()
  const { company } = useOutletContext<{ company: CompanyProfile | null }>()
  const [traces, setTraces] = useState<AgentTrace[]>([])
  const [research, setResearch] = useState<MemoryHit[]>([])
  const [reflection, setReflection] = useState<MemoryHit | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isRunningAnalytics, setIsRunningAnalytics] = useState(false)
  const [error, setError] = useState("")

  const loadDashboard = useCallback(async () => {
    setIsLoading(true)
    const [traceResult, researchResult, reflectionResult] = await Promise.allSettled([
      getAgentTraces(50),
      getResearchMemories(50),
      getLatestAnalyticsReflection(),
    ])
    const failed: string[] = []
    if (traceResult.status === "fulfilled") setTraces(traceResult.value)
    else failed.push("agent activity")
    if (researchResult.status === "fulfilled") setResearch(researchResult.value)
    else failed.push("market research")
    if (reflectionResult.status === "fulfilled") setReflection(reflectionResult.value)
    else failed.push("analytics reflection")
    setError(failed.length > 0 ? `Could not load ${failed.join(", ")}.` : "")
    setIsLoading(false)
  }, [])

  useEffect(() => {
    void loadDashboard()
  }, [loadDashboard])

  async function handleRunAnalytics() {
    if (isRunningAnalytics) return
    setIsRunningAnalytics(true)
    setError("")
    try {
      await runAnalyticsReflection("theme")
      setReflection(await getLatestAnalyticsReflection())
      setTraces(await getAgentTraces(50))
    } catch (runError) {
      setError(runError instanceof Error ? runError.message : "Analytics could not be completed.")
    } finally {
      setIsRunningAnalytics(false)
    }
  }

  const groups = useMemo(() => analyticsGroups(reflection), [reflection])
  const bestGroup = typeof reflection?.metadata.best_group === "string" ? reflection.metadata.best_group : null
  const successfulRuns = traces.filter((trace) => trace.success).length
  const contentRuns = traces.filter((trace) => trace.agent_name === "content" && trace.success).length
  const stats = [
    { label: "Recent agent runs", value: traces.length, detail: `${successfulRuns} successful` },
    { label: "Research memories", value: research.length, detail: "saved findings" },
    { label: "Generated outputs", value: contentRuns, detail: "recent content runs" },
    { label: "Analytics reflection", value: reflection ? "Ready" : "Not yet", detail: reflection ? "saved to memory" : "run analytics below" },
  ]

  return <section className="live-dashboard" aria-labelledby="dashboard-heading">
    <header className="dashboard-page-heading">
      <div>
        <p className="dashboard-kicker">LIVE COMPANY WORKSPACE</p>
        <h1 id="dashboard-heading">Dashboard</h1>
        <p className="dashboard-welcome">Welcome back{company?.name ? `, ${company.name}` : ""}. Every number below comes from your APIs.</p>
      </div>
      <button type="button" className="secondary-action" onClick={() => void loadDashboard()} disabled={isLoading}>
        {isLoading ? "Refreshing…" : "Refresh data"}
      </button>
    </header>

    {error && <div className="form-error" role="alert">{error}</div>}

    <div className="dashboard-kpi-grid" style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 14 }}>
      {stats.map((stat) => <article className="live-stat" key={stat.label} style={card}>
        <span>{stat.label}</span>
        <strong>{stat.value}</strong>
        <small>{stat.detail}</small>
      </article>)}
    </div>

    <div className="dashboard-main-grid" style={{ display: "grid", gridTemplateColumns: "1.1fr .9fr", gap: 16 }}>
      <article style={card}>
        <div className="card-heading-row">
          <div><p className="dashboard-kicker">T20 TRACE OUTPUT</p><h2>Recent Agent Activity</h2></div>
          <button type="button" className="text-action" onClick={() => navigate("/dashboard/activity")}>View all →</button>
        </div>
        {traces.length === 0 ? <div className="inline-empty">No agent runs recorded yet.</div> : <div className="activity-preview-list">
          {traces.slice(0, 5).map((trace) => <div key={trace.id}>
            <span className={`trace-dot trace-dot-${trace.success ? "success" : "failure"}`} />
            <div><strong>{readable(trace.agent_name)}</strong><small>{trace.memories_retrieved.length} memories · {Math.round(trace.duration_ms)} ms</small></div>
            <time>{formatTime(trace.created_at)}</time>
          </div>)}
        </div>}
      </article>

      <article style={card}>
        <div className="card-heading-row">
          <div><p className="dashboard-kicker">MARKET RESEARCH MEMORY</p><h2>Latest Findings</h2></div>
          <button type="button" className="text-action" onClick={() => navigate("/dashboard/market")}>Open research →</button>
        </div>
        {research.length === 0 ? <div className="inline-empty">No saved research yet. Run the Market Research Agent to populate this area.</div> : <div className="research-preview-list">
          {research.slice(0, 4).map((memory) => <div key={memory.id}>
            <span>{typeof memory.metadata.category === "string" ? readable(memory.metadata.category) : "Research"}</span>
            <p>{memory.content}</p>
          </div>)}
        </div>}
      </article>
    </div>

    <article style={card}>
      <div className="card-heading-row analytics-live-heading">
        <div><p className="dashboard-kicker">T21 ANALYTICS & REFLECTION</p><h2>Campaign performance → reusable memory</h2></div>
        <div className="analytics-status-actions">
          <span className={`reflection-status reflection-status-${reflection ? "ready" : "missing"}`}>
            {reflection ? "✓ Saved as reflection memory" : "No reflection saved"}
          </span>
          <button type="button" className="analytics-run-button" disabled={isRunningAnalytics} onClick={() => void handleRunAnalytics()}>
            {isRunningAnalytics ? "Analyzing…" : reflection ? "Refresh analysis" : "Run analytics"}
          </button>
        </div>
      </div>

      {!reflection ? <div className="analytics-empty">
        <strong>No analytics output yet.</strong>
        <span>The agent requires at least two valid simulated, published LinkedIn performance memories across two themes.</span>
      </div> : <div className="analytics-live-grid">
        <div>
          <h3>Measured groups</h3>
          {groups.length === 0 ? <div className="inline-empty">This saved reflection predates structured aggregate metadata. Refresh analysis to generate measured groups.</div> : groups.map((group) => <div className={`analytics-group ${group.group_name === bestGroup ? "analytics-group-best" : ""}`} key={group.group_name}>
            <div><strong>{readable(group.group_name)}</strong>{group.group_name === bestGroup && <span>Best</span>}</div>
            <p>{group.total_likes} likes · {group.total_comments} comments · {group.total_clicks} clicks</p>
            <small>Average engagement/post: {group.average_engagement_per_post}</small>
          </div>)}
        </div>
        <div className="reflection-output">
          <h3>Saved reflection</h3>
          <p>{reflection.content}</p>
          <small>{new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(reflection.created_at))}</small>
        </div>
        <div className="analytics-next-action">
          <h3>Close the loop</h3>
          <p>Generate the next post with this reflection in the Content Agent’s retrieved memory context.</p>
          <button type="button" onClick={() => navigate("/dashboard/content", { state: { prompt: "Create a LinkedIn post using our latest campaign reflection. Test a different opening hook and keep the recommendation grounded in that reflection." } })}>
            Use reflection in Content →
          </button>
        </div>
      </div>}
    </article>
  </section>
}
