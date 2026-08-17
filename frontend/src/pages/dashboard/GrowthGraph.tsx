import { useState } from "react"
import { ApiError } from "@/api/client"
import {
  getGrowthGraphInsights,
  type GrowthGraphResponse,
} from "@/api/growthgraph"

const SUGGESTED_QUERIES = [
  "What challenges are founders facing around product-market fit?",
  "Which go-to-market problems appear most often across the cohort?",
  "What customer acquisition themes are emerging across founders?",
]

function percentage(value: number | null) {
  if (value == null) return "—"
  return `${Math.round(Math.max(0, Math.min(1, value)) * 100)}%`
}

export default function GrowthGraph() {
  const [query, setQuery] = useState(SUGGESTED_QUERIES[0])
  const [result, setResult] = useState<GrowthGraphResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")

  async function runQuery(rawQuery = query) {
    const normalized = rawQuery.trim()
    if (!normalized || isLoading) return

    setQuery(normalized)
    setError("")
    setIsLoading(true)
    try {
      setResult(await getGrowthGraphInsights(normalized))
    } catch (requestError) {
      if (requestError instanceof ApiError && requestError.status === 404) {
        setError("The GrowthGraph query service is not connected yet. The frontend contract is ready for the T36 backend endpoint.")
      } else {
        setError(requestError instanceof Error ? requestError.message : "GrowthGraph could not load this insight.")
      }
    } finally {
      setIsLoading(false)
    }
  }

  const insights = result?.insights || []

  return (
    <section className="growthgraph-page" aria-labelledby="growthgraph-heading">
      <header className="dashboard-page-heading">
        <div>
          <p className="dashboard-kicker">PRIVACY-SAFE COHORT INTELLIGENCE</p>
          <h1 id="growthgraph-heading">GrowthGraph</h1>
        </div>
        <span className="privacy-badge">◈ Anonymous aggregate only</span>
      </header>

      <div className="growthgraph-hero">
        <div>
          <span className="growthgraph-eyebrow">Learn from the network, not from another founder’s raw data</span>
          <h2>See which challenges repeat across the founder cohort.</h2>
          <p>GrowthGraph compares vector patterns across an allowlisted cohort and returns aggregate themes. Company names, tenant IDs, and source memories never appear here.</p>
        </div>
        <div className="privacy-rules" aria-label="GrowthGraph privacy guarantees">
          <span>✓ Cohort-level counts</span>
          <span>✓ Anonymous themes</span>
          <span>✓ No raw memories</span>
          <span>✓ No company identities</span>
        </div>
      </div>

      <form className="growthgraph-query" onSubmit={(event) => { event.preventDefault(); void runQuery() }}>
        <label htmlFor="growthgraph-query">Ask a cross-founder question</label>
        <div>
          <input
            id="growthgraph-query"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            disabled={isLoading}
            placeholder="e.g. What blocks founders from finding product-market fit?"
          />
          <button type="submit" disabled={isLoading || !query.trim()}>
            {isLoading ? "Finding patterns…" : "Find cohort patterns →"}
          </button>
        </div>
      </form>

      <div className="growthgraph-suggestions">
        {SUGGESTED_QUERIES.map((suggestion) => (
          <button key={suggestion} type="button" disabled={isLoading} onClick={() => void runQuery(suggestion)}>
            {suggestion}
          </button>
        ))}
      </div>

      {error && <div className="form-error growthgraph-error" role="alert">{error}</div>}

      {!result && !error && (
        <div className="growthgraph-empty">
          <div>◎</div>
          <strong>Ready for an anonymous cohort query</strong>
          <span>Choose a focused question to generate one demo-safe aggregate insight.</span>
        </div>
      )}

      {result && (
        <div className="growthgraph-results" aria-live="polite">
          <div className="growthgraph-result-heading">
            <div>
              <span>QUERY</span>
              <h2>{result.query}</h2>
            </div>
            <div className="cohort-stat">
              <strong>{result.cohort_size}</strong>
              <span>founders in anonymized cohort</span>
            </div>
          </div>

          {result.insight && <article className="growthgraph-primary-insight">
            <span>AGGREGATE INSIGHT</span>
            <p>{result.insight}</p>
          </article>}

          {insights.length > 0 && <div className="growthgraph-insight-grid">
            {insights.map((insight, index) => (
              <article key={`${insight.theme}-${index}`} className="growthgraph-insight-card">
                <header>
                  <span>Theme {index + 1}</span>
                  <strong>{insight.theme}</strong>
                </header>
                <p>{insight.summary}</p>
                <dl>
                  <div><dt>Matched founders</dt><dd>{insight.matched_founders}</dd></div>
                  <div><dt>Cohort prevalence</dt><dd>{percentage(insight.prevalence)}</dd></div>
                  <div><dt>Avg. similarity</dt><dd>{percentage(insight.average_similarity)}</dd></div>
                </dl>
              </article>
            ))}
          </div>}

          {!result.insight && insights.length === 0 && (
            <div className="growthgraph-empty"><strong>No cohort pattern met the safe reporting threshold.</strong></div>
          )}

          <p className="growthgraph-disclosure">Results are aggregated across an allowlisted cohort. They are directional signals, not verified market facts.</p>
        </div>
      )}
    </section>
  )
}
