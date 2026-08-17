import type { CSSProperties } from "react"

const card: CSSProperties = {
  background: "rgba(255,255,255,0.5)",
  border: "1.5px solid rgba(255,255,255,0.65)",
  borderRadius: 16,
  padding: "20px",
  backdropFilter: "blur(6px)",
}

const COMPETITORS = [
  { name: "Competitor.io", score: 82, strength: "Strong brand awareness", weakness: "Weak onboarding UX" },
  { name: "GrowBase", score: 71, strength: "Deep GTM templates", weakness: "No AI assistant" },
  { name: "StrategyAI", score: 68, strength: "Fast content gen", weakness: "No market research" },
]

const REDDIT_POSTS = [
  { sub: "r/startups", signal: "Pain", text: "Why does every GTM tool assume you already know your ICP? We need help figuring that out first.", upvotes: 847 },
  { sub: "r/SaaS", signal: "Pain", text: "AI content generators are useless without strategic context. It's just word salad unless the AI knows your market.", upvotes: 412 },
  { sub: "r/Entrepreneur", signal: "Signal", text: "Founder who added positioning clarity to their pitch saw close rate go from 14% → 38% in one quarter.", upvotes: 1204 },
]

const PAIN_POINTS = [
  "Founders don't know how to differentiate from funded competitors",
  "ICP is too broad — every feature is built for 'everyone'",
  "Content doesn't resonate because messaging isn't positioning-led",
  "No systematic way to track competitor moves and adapt strategy",
]

const TRENDS = [
  { name: "AI-native GTM tools", growth: "+187% YoY" },
  { name: "Founder-led sales content", growth: "+94% YoY" },
  { name: "Positioning-first frameworks", growth: "+63% YoY" },
  { name: "Market intelligence SaaS", growth: "+121% YoY" },
]

export default function MarketResearch() {
  return (
    <div style={{ fontFamily: "'Oranienbaum', serif" }}>
      <h1 style={{
        fontFamily: "'Playfair Display', serif",
        fontSize: 28,
        fontWeight: 700,
        color: "#0d2137",
        margin: "0 0 24px",
        background: "rgba(74,122,181,0.15)",
        display: "inline-block",
        padding: "6px 16px",
        borderRadius: 8,
      }}>
        Market Research
      </h1>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
        {/* Competitor Analysis */}
        <div style={card}>
          <h2 style={{ fontSize: 17, fontWeight: 700, color: "#0d2137", margin: "0 0 16px" }}>Competitor Analysis</h2>
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {COMPETITORS.map((c) => (
              <div key={c.name} style={{ borderBottom: "1px solid rgba(74,122,181,0.12)", paddingBottom: 12 }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                  <span style={{
                    fontSize: 15, fontWeight: 600, background: "rgba(74,122,181,0.15)",
                    color: "#0d2137", borderRadius: 6, padding: "3px 10px",
                  }}>{c.name}</span>
                  <span style={{
                    fontSize: 13, fontWeight: 700, background: c.score >= 80 ? "rgba(239,68,68,0.12)" : "rgba(74,122,181,0.12)",
                    color: c.score >= 80 ? "#dc2626" : "#2d5a8e",
                    borderRadius: 6, padding: "3px 10px",
                  }}>Score: {c.score}</span>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6 }}>
                  <div style={{ background: "rgba(34,197,94,0.1)", borderRadius: 6, padding: "5px 10px", fontSize: 12, color: "#166534" }}>
                    ↑ {c.strength}
                  </div>
                  <div style={{ background: "rgba(239,68,68,0.1)", borderRadius: 6, padding: "5px 10px", fontSize: 12, color: "#991b1b" }}>
                    ↓ {c.weakness}
                  </div>
                </div>
                <div style={{ marginTop: 6, height: 3, background: "rgba(74,122,181,0.12)", borderRadius: 2 }}>
                  <div style={{ height: "100%", width: `${c.score}%`, background: "#4a7ab5", borderRadius: 2 }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Reddit Discussions */}
        <div style={card}>
          <h2 style={{ fontSize: 17, fontWeight: 700, color: "#0d2137", margin: "0 0 16px" }}>Reddit Discussions</h2>
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {REDDIT_POSTS.map((post, i) => (
              <div key={i} style={{ borderBottom: "1px solid rgba(74,122,181,0.12)", paddingBottom: 12 }}>
                <div style={{ display: "flex", gap: 8, marginBottom: 6 }}>
                  <span style={{
                    fontSize: 12, fontWeight: 600, color: "#ff6b35",
                    background: "rgba(255,107,53,0.1)", borderRadius: 5, padding: "2px 8px",
                  }}>{post.sub}</span>
                  <span style={{
                    fontSize: 12, fontWeight: 600,
                    background: post.signal === "Pain" ? "rgba(239,68,68,0.1)" : "rgba(34,197,94,0.1)",
                    color: post.signal === "Pain" ? "#dc2626" : "#166534",
                    borderRadius: 5, padding: "2px 8px",
                  }}>{post.signal}</span>
                </div>
                <div style={{
                  background: "rgba(74,122,181,0.1)",
                  borderRadius: 8,
                  padding: "10px 12px",
                  fontSize: 15,
                  color: "#0d2137",
                  lineHeight: 1.45,
                  marginBottom: 6,
                }}>
                  "{post.text}"
                </div>
                <span style={{ fontSize: 12, color: "#4a7ab5", fontWeight: 600 }}>▲ {post.upvotes.toLocaleString()} upvotes</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        {/* Customer Pain Points */}
        <div style={card}>
          <h2 style={{ fontSize: 17, fontWeight: 700, color: "#0d2137", margin: "0 0 14px" }}>Customer Pain Points</h2>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {PAIN_POINTS.map((p, i) => (
              <div key={i} style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
                <div style={{
                  width: 20, height: 20, borderRadius: 5,
                  background: "#4a7ab5", color: "#fff",
                  fontSize: 11, fontWeight: 700,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  flexShrink: 0, marginTop: 1,
                }}>
                  {i + 1}
                </div>
                <div style={{
                  flex: 1, background: "rgba(74,122,181,0.1)",
                  borderRadius: 8, padding: "8px 12px",
                  fontSize: 15, color: "#1a3a5c", lineHeight: 1.45,
                }}>
                  {p}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Market Trends */}
        <div style={card}>
          <h2 style={{ fontSize: 17, fontWeight: 700, color: "#0d2137", margin: "0 0 14px" }}>Market Trends & Insights</h2>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {TRENDS.map((t, i) => (
              <div key={i} style={{
                display: "flex", justifyContent: "space-between", alignItems: "center",
                background: "rgba(74,122,181,0.1)", borderRadius: 8, padding: "10px 14px",
              }}>
                <span style={{ fontSize: 15, fontWeight: 600, color: "#0d2137" }}>{t.name}</span>
                <span style={{
                  fontSize: 12, fontWeight: 700,
                  background: "rgba(34,197,94,0.15)",
                  color: "#166534",
                  borderRadius: 6, padding: "3px 10px",
                }}>{t.growth}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
