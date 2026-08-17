import { useNavigate } from "react-router-dom"
import type { CSSProperties } from "react"

const NEWS = [
  {
    tag: "AI & SaaS",
    timestamp: "2h ago",
    headline: "OpenAI launches operator-mode GPT for enterprise positioning teams",
    summary: "New API endpoints let businesses embed context-aware growth agents directly into their CRM workflows.",
    img: "https://images.unsplash.com/photo-1677442135068-5d67a0f4c38d?w=80&h=80&fit=crop&auto=format",
  },
  {
    tag: "B2B Marketing",
    timestamp: "5h ago",
    headline: "LinkedIn engagement rates for thought-leadership posts up 34% in Q3 2026",
    summary: "Long-form carousel posts outperform text-only by 2.4×. Founders posting 3×/week see highest inbound.",
    img: "https://images.unsplash.com/photo-1611944212129-29977ae1398c?w=80&h=80&fit=crop&auto=format",
  },
  {
    tag: "Funding",
    timestamp: "1d ago",
    headline: "Series A rounds in AI-native SaaS average $14M — up from $8M in 2025",
    summary: "Investors are prioritizing GTM clarity and retention metrics over raw ARR growth in current climate.",
    img: "https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?w=80&h=80&fit=crop&auto=format",
  },
  {
    tag: "Product",
    timestamp: "2d ago",
    headline: "Positioning-first companies show 40% lower CAC than feature-led peers",
    summary: "A new Reforge study confirms that clear ICP definition at pre-seed reduces paid acquisition costs.",
    img: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=80&h=80&fit=crop&auto=format",
  },
]

const WEEKLY_DATA = [42, 58, 51, 67, 74, 82]
const WEEKS = ["W1", "W2", "W3", "W4", "W5", "W6"]

const TIPS = [
  "Refine your ICP by adding a 'Job to be Done' framing to each persona.",
  "Your LinkedIn post frequency is below target — aim for 3 posts this week.",
  "Update your positioning statement with Q3 competitor movements.",
]

const KPI = [
  { label: "Growth Score", value: "74", unit: "/ 100", color: "#4a7ab5" },
  { label: "Leads This Week", value: "142", unit: "total", color: "#2d8a4e" },
  { label: "Content Pieces", value: "38", unit: "published", color: "#6d28d9" },
]

const ANALYTICS_TOPICS = [
  { topic: "Engineering workflows", likes: 119, comments: 26, clicks: 53, avg: 99 },
  { topic: "AI automation", likes: 44, comments: 8, clicks: 18, avg: 35 },
]

const card: CSSProperties = {
  background: "rgba(255,255,255,0.5)",
  border: "1.5px solid rgba(255,255,255,0.65)",
  borderRadius: 16,
  padding: "20px",
  backdropFilter: "blur(6px)",
}

export default function DashboardHome() {
  const navigate = useNavigate()
  const maxVal = Math.max(...WEEKLY_DATA)

  return (
    <div style={{ fontFamily: "'Oranienbaum', serif", display: "flex", flexDirection: "column", gap: 20 }}>

      {/* Page title */}
      <div>
        <h1 style={{ fontFamily: "'Playfair Display', serif", fontSize: 30, fontWeight: 700, color: "#0d2137", margin: "0 0 4px" }}>
          Dashboard
        </h1>
        <p style={{ fontFamily: "'Oranienbaum', serif", fontSize: 16, color: "rgb(255,255,255)", margin: 0 }}>
          Good morning, Jane — here's what's happening in your market today.
        </p>
      </div>

      {/* ── Row 1: KPI stat tiles ── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14 }}>
        {KPI.map(k => (
          <div key={k.label} style={{
            ...card,
            padding: "18px 22px",
            display: "flex",
            alignItems: "center",
            gap: 16,
          }}>
            <div style={{
              width: 48, height: 48, borderRadius: 12,
              background: k.color + "1a",
              border: `1.5px solid ${k.color}33`,
              display: "flex", alignItems: "center", justifyContent: "center",
              flexShrink: 0,
            }}>
              <div style={{ width: 18, height: 18, borderRadius: 4, background: k.color }} />
            </div>
            <div>
              <p style={{ margin: "0 0 2px", fontFamily: "'Oranienbaum', serif", fontSize: 15, color: "#4a7ab5" }}>{k.label}</p>
              <p style={{ margin: 0, fontFamily: "'Playfair Display', serif", fontSize: 26, fontWeight: 700, color: "#0d2137", lineHeight: 1 }}>
                {k.value} <span style={{ fontSize: 15, fontWeight: 400, color: "#8aa8c8" }}>{k.unit}</span>
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* ── Row 2: News feed (left) + Growth chart & Tips (right) ── */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 360px", gap: 16, alignItems: "start" }}>

        {/* News feed */}
        <div style={card}>
          <h2 style={{ fontFamily: "'Playfair Display', serif", fontSize: 17, fontWeight: 700, color: "#0d2137", margin: "0 0 16px" }}>
            News Around the Business
          </h2>
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {NEWS.map((item, i) => (
              <div
                key={i}
                style={{
                  display: "flex",
                  gap: 14,
                  padding: "14px",
                  borderRadius: 12,
                  cursor: "pointer",
                  transition: "all 0.2s",
                  background: "rgba(74,122,181,0.04)",
                  border: "1px solid rgba(74,122,181,0.08)",
                }}
                onMouseEnter={e => { e.currentTarget.style.background = "rgba(74,122,181,0.1)"; e.currentTarget.style.transform = "translateX(3px)" }}
                onMouseLeave={e => { e.currentTarget.style.background = "rgba(74,122,181,0.04)"; e.currentTarget.style.transform = "translateX(0)" }}
              >
                <img
                  src={item.img}
                  alt={item.tag}
                  style={{ width: 50, height: 50, borderRadius: 10, objectFit: "cover", flexShrink: 0, backgroundColor: "#4a7ab5" }}
                />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: "flex", gap: 8, marginBottom: 5, alignItems: "center" }}>
                    <span style={{
                      fontSize: 15, fontWeight: 700, background: "rgba(74,122,181,0.15)",
                      color: "#2d5a8e", borderRadius: 4, padding: "2px 7px", whiteSpace: "nowrap",
                    }}>{item.tag}</span>
                    <span style={{ fontSize: 15, color: "#8aa8c8" }}>{item.timestamp}</span>
                  </div>
                  <p style={{ margin: "0 0 3px", fontFamily: "'Oranienbaum', serif", fontWeight: 600, fontSize: 15, color: "#0d2137", lineHeight: 1.4 }}>{item.headline}</p>
                  <p style={{ margin: 0, fontFamily: "'Oranienbaum', serif", fontSize: 15, color: "#2d5a8e", lineHeight: 1.4 }}>{item.summary}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right column: Growth chart + Tips */}
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>

          {/* Weekly Growth Report */}
          <div style={card}>
            <h3 style={{ fontFamily: "'Playfair Display', serif", fontSize: 17, fontWeight: 700, color: "#0d2137", margin: "0 0 14px" }}>
              Weekly Growth Report
            </h3>

            {/* Bar chart */}
            <div style={{ display: "flex", alignItems: "flex-end", gap: 5, height: 72, marginBottom: 6 }}>
              {WEEKLY_DATA.map((val, i) => (
                <div key={i} style={{ flex: 1, height: "100%", display: "flex", flexDirection: "column", justifyContent: "flex-end" }}>
                  <div style={{
                    width: "100%",
                    height: `${(val / maxVal) * 100}%`,
                    background: i === WEEKLY_DATA.length - 1 ? "#4a7ab5" : "rgba(74,122,181,0.28)",
                    borderRadius: "4px 4px 0 0",
                  }} />
                </div>
              ))}
            </div>
            <div style={{ display: "flex", gap: 5, marginBottom: 14 }}>
              {WEEKS.map(w => (
                <div key={w} style={{ flex: 1, textAlign: "center", fontSize: 15, color: "#8aa8c8", fontWeight: 600 }}>{w}</div>
              ))}
            </div>

            {/* Metric row */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
              {[
                { label: "Score", value: "74" },
                { label: "Leads", value: "142" },
                { label: "Posts", value: "38" },
              ].map(m => (
                <div key={m.label} style={{
                  background: "rgba(74,122,181,0.1)",
                  borderRadius: 8,
                  padding: "8px 6px",
                  textAlign: "center",
                }}>
                  <p style={{ margin: "0 0 2px", fontSize: 15, color: "#4a7ab5", fontWeight: 600 }}>{m.label}</p>
                  <p style={{ margin: 0, fontFamily: "'Playfair Display', serif", fontSize: 20, fontWeight: 700, color: "#0d2137" }}>{m.value}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Tips for Improvement */}
          <div style={card}>
            <h3 style={{ fontFamily: "'Playfair Display', serif", fontSize: 17, fontWeight: 700, color: "#0d2137", margin: "0 0 14px" }}>
              Tips for Improvement
            </h3>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {TIPS.map((tip, i) => (
                <div
                  key={i}
                  style={{ display: "flex", gap: 10, alignItems: "flex-start", cursor: "pointer" }}
                  onClick={() => navigate("/dashboard/ai-partner")}
                >
                  <div style={{
                    width: 22, height: 22, borderRadius: 6,
                    background: "#4a7ab5", color: "#fff",
                    fontSize: 12, fontWeight: 700,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    flexShrink: 0, marginTop: 1,
                  }}>!</div>
                  <div
                    style={{
                      flex: 1,
                      background: "rgba(74,122,181,0.08)",
                      borderRadius: 8,
                      padding: "8px 12px",
                      fontFamily: "'Oranienbaum', serif",
                      fontSize: 15,
                      color: "#1a3a5c",
                      lineHeight: 1.45,
                      transition: "background 0.2s",
                    }}
                    onMouseEnter={e => (e.currentTarget.style.background = "rgba(74,122,181,0.16)")}
                    onMouseLeave={e => (e.currentTarget.style.background = "rgba(74,122,181,0.08)")}
                  >
                    {tip}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── Row 3: Analytics & Reflection ── */}
      <div style={card}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 18 }}>
          <div>
            <h3 style={{ fontFamily: "'Playfair Display', serif", fontSize: 17, fontWeight: 700, color: "#0d2137", margin: "0 0 3px" }}>
              Analytics & Reflection
            </h3>
            <p style={{ margin: 0, fontFamily: "'Oranienbaum', serif", fontSize: 15, color: "rgb(24,25,26)" }}>
              Simulated demo data
            </p>
          </div>
          <span style={{
            fontFamily: "'Oranienbaum', serif",
            fontSize: 11, fontWeight: 700,
            color: "#6d28d9",
            background: "rgba(109,40,217,0.1)",
            border: "1px solid rgba(109,40,217,0.22)",
            borderRadius: 12,
            padding: "4px 10px",
          }}>
            ✓ Saved as reflection memory
          </span>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>

          {/* Topic comparison */}
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <p style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 700, color: "#4a7ab5", textTransform: "uppercase", letterSpacing: "0.06em" }}>
              Content performance
            </p>
            {ANALYTICS_TOPICS.map((row, i) => (
              <div key={i} style={{
                background: i === 0 ? "rgba(74,122,181,0.1)" : "rgba(74,122,181,0.04)",
                border: i === 0 ? "1.5px solid rgba(74,122,181,0.22)" : "1px solid rgba(74,122,181,0.1)",
                borderRadius: 10,
                padding: "12px 14px",
              }}>
                <p style={{ margin: "0 0 6px", fontFamily: "'Playfair Display', serif", fontSize: 15, fontWeight: 700, color: "#0d2137" }}>
                  {row.topic}
                </p>
                <p style={{ margin: "0 0 3px", fontFamily: "'Oranienbaum', serif", fontSize: 15, color: "#4a7ab5" }}>
                  {row.likes} likes · {row.comments} comments · {row.clicks} clicks
                </p>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 6 }}>
                  <span style={{ fontFamily: "'Oranienbaum', serif", fontSize: 15, color: "#2d5a8e", fontWeight: 600 }}>
                    Avg engagement/post
                  </span>
                  <span style={{
                    fontFamily: "'Playfair Display', serif",
                    fontSize: 18, fontWeight: 700,
                    color: i === 0 ? "#2d8a4e" : "#0d2137",
                  }}>{row.avg}</span>
                </div>
              </div>
            ))}
          </div>

          {/* Insight + Reflection */}
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <p style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 700, color: "#4a7ab5", textTransform: "uppercase", letterSpacing: "0.06em" }}>
              Insight & Reflection
            </p>
            <div style={{
              background: "rgba(34,197,94,0.08)",
              border: "1.5px solid rgba(34,197,94,0.22)",
              borderRadius: 10,
              padding: "12px 14px",
            }}>
              <p style={{ margin: "0 0 4px", fontSize: 15, fontWeight: 700, color: "#166534", textTransform: "uppercase", letterSpacing: "0.05em" }}>Insight</p>
              <p style={{ margin: 0, fontFamily: "'Oranienbaum', serif", fontSize: 15, color: "#166534", lineHeight: 1.5 }}>
                Engineering workflow content generated <strong>2.8×</strong> more engagement per post.
              </p>
            </div>
            <div style={{
              background: "rgba(74,122,181,0.06)",
              border: "1px solid rgba(74,122,181,0.14)",
              borderRadius: 10,
              padding: "12px 14px",
              flex: 1,
            }}>
              <p style={{ margin: "0 0 4px", fontSize: 15, fontWeight: 700, color: "#2d5a8e", textTransform: "uppercase", letterSpacing: "0.05em" }}>Reflection</p>
              <p style={{ margin: 0, fontFamily: "'Oranienbaum', serif", fontSize: 15, color: "#1a3a5c", lineHeight: 1.5 }}>
                Posts addressing concrete workflow friction appeared more relevant than general AI automation lists. Hypothesis based on simulated data.
              </p>
            </div>
          </div>

          {/* Next experiment + CTA */}
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <p style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 700, color: "#4a7ab5", textTransform: "uppercase", letterSpacing: "0.06em" }}>
              Next Steps
            </p>
            <div style={{
              background: "rgba(74,122,181,0.06)",
              border: "1px solid rgba(74,122,181,0.14)",
              borderRadius: 10,
              padding: "12px 14px",
              flex: 1,
            }}>
              <p style={{ margin: "0 0 4px", fontSize: 15, fontWeight: 700, color: "#2d5a8e", textTransform: "uppercase", letterSpacing: "0.05em" }}>Next Experiment</p>
              <p style={{ margin: 0, fontFamily: "'Oranienbaum', serif", fontSize: 15, color: "#1a3a5c", lineHeight: 1.5 }}>
                Test another workflow-focused post with a different opening hook to validate the 2.8× finding.
              </p>
            </div>
            <button
              onClick={() => navigate("/dashboard/content")}
              style={{
                width: "100%",
                background: "#0d2137",
                border: "none",
                color: "#fff",
                borderRadius: 10,
                padding: "13px 16px",
                fontFamily: "'Oranienbaum', serif",
                fontWeight: 600,
                fontSize: 15,
                cursor: "pointer",
                transition: "background 0.2s",
                textAlign: "center",
              }}
              onMouseEnter={e => (e.currentTarget.style.background = "#1a3a5c")}
              onMouseLeave={e => (e.currentTarget.style.background = "#0d2137")}
            >
              Use this insight for the next LinkedIn post →
            </button>
          </div>
        </div>
      </div>

    </div>
  )
}
