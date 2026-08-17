import type { CSSProperties } from "react"

const card: CSSProperties = {
  background: "rgba(255,255,255,0.5)",
  border: "1.5px solid rgba(255,255,255,0.65)",
  borderRadius: 16,
  padding: "20px",
  backdropFilter: "blur(6px)",
}

const PERSONAS = [
  { initials: "SM", name: "Sarah M. — Head of Growth", goal: "Needs to scale inbound without growing the team" },
  { initials: "JR", name: "James R. — Founding CEO", goal: "Wants a credible market position before Series A" },
  { initials: "AK", name: "Anika K. — Solo Founder", goal: "Overwhelmed by GTM — needs a clear starting point" },
]

const CHANNELS = [
  { name: "LinkedIn (Founder-led)", fit: "High", effort: "Low", rank: "#1" },
  { name: "Cold email (ICP-targeted)", fit: "High", effort: "Med", rank: "#2" },
  { name: "SEO / Content hub", fit: "High", effort: "High", rank: "#3" },
  { name: "Community (Slack/Reddit)", fit: "Med", effort: "Low", rank: "#4" },
  { name: "Partner co-marketing", fit: "Med", effort: "Med", rank: "#5" },
]

const PHASES = [
  {
    label: "Phase 1: Awareness",
    color: "rgba(45,90,142,0.7)",
    actions: [
      "Publish positioning article on LinkedIn",
      "Launch ICP cold email campaign",
      "Set up tracking pixels + UTMs",
    ],
  },
  {
    label: "Phase 2: Activation",
    color: "rgba(74,122,181,0.7)",
    actions: [
      "Onboarding sequence (5 emails)",
      "Run 10 discovery calls",
      "A/B test landing page headline",
    ],
  },
  {
    label: "Phase 3: Scale",
    color: "rgba(107,159,212,0.7)",
    actions: [
      "Build referral program",
      "Expand to partner channels",
      "Launch case study content series",
    ],
  },
]

export default function GTMStrategy() {
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
        GTM Strategy
      </h1>

      {/* Positioning statement */}
      <div style={{ ...card, marginBottom: 16 }}>
        <h2 style={{ fontSize: 17, fontWeight: 700, color: "#0d2137", margin: "0 0 12px" }}>Positioning Statement</h2>
        <div style={{
          background: "rgba(74,122,181,0.1)",
          borderRadius: 10,
          padding: "16px 20px",
          fontStyle: "italic",
          fontSize: 15,
          color: "#0d2137",
          textAlign: "center",
          lineHeight: 1.6,
          border: "1px solid rgba(74,122,181,0.15)",
        }}>
          For <strong>early-stage B2B SaaS founders</strong> who need a clear path to market,{" "}
          <strong>GrowthPilot</strong> is the AI-powered growth platform that delivers{" "}
          <strong>strategic positioning, market intelligence, and ready-to-use content</strong> —
          unlike generic AI tools that lack business context and strategic depth.
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
        {/* Customer Personas */}
        <div style={card}>
          <h2 style={{ fontSize: 17, fontWeight: 700, color: "#0d2137", margin: "0 0 16px" }}>Customer Personas</h2>
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {PERSONAS.map((p) => (
              <div key={p.initials} style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
                <div style={{
                  width: 36, height: 36, borderRadius: "50%",
                  background: "#4a7ab5", color: "#fff",
                  fontWeight: 700, fontSize: 13,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  flexShrink: 0,
                }}>
                  {p.initials}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{
                    background: "rgba(74,122,181,0.12)",
                    borderRadius: 6, padding: "5px 10px",
                    fontSize: 15, fontWeight: 600, color: "#0d2137",
                    marginBottom: 5,
                  }}>{p.name}</div>
                  <div style={{
                    background: "rgba(74,122,181,0.08)",
                    borderRadius: 6, padding: "5px 10px",
                    fontSize: 15, color: "#2d5a8e",
                  }}>{p.goal}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Launch Channels */}
        <div style={card}>
          <h2 style={{ fontSize: 17, fontWeight: 700, color: "#0d2137", margin: "0 0 14px" }}>Launch Channels (ranked by fit)</h2>
          <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
            <div style={{
              display: "grid", gridTemplateColumns: "2fr 80px 80px 48px",
              gap: 8, padding: "6px 0", borderBottom: "1px solid rgba(74,122,181,0.15)",
              marginBottom: 6,
            }}>
              {["Channel", "Fit", "Effort", "#"].map(h => (
                <span key={h} style={{ fontSize: 11, fontWeight: 700, color: "#4a7ab5", letterSpacing: "0.06em", textTransform: "uppercase" }}>{h}</span>
              ))}
            </div>
            {CHANNELS.map((ch) => (
              <div key={ch.name} style={{
                display: "grid", gridTemplateColumns: "2fr 80px 80px 48px",
                gap: 8, marginBottom: 6,
              }}>
                <div style={{
                  background: "rgba(74,122,181,0.1)", borderRadius: 6,
                  padding: "6px 10px", fontSize: 12, color: "#0d2137", fontWeight: 500,
                }}>{ch.name}</div>
                <div style={{
                  background: ch.fit === "High" ? "rgba(34,197,94,0.12)" : "rgba(234,179,8,0.12)",
                  borderRadius: 6, padding: "6px 10px",
                  fontSize: 12, color: ch.fit === "High" ? "#166534" : "#854d0e",
                  fontWeight: 600, textAlign: "center",
                }}>{ch.fit}</div>
                <div style={{
                  background: ch.effort === "Low" ? "rgba(34,197,94,0.12)" : ch.effort === "Med" ? "rgba(234,179,8,0.12)" : "rgba(239,68,68,0.1)",
                  borderRadius: 6, padding: "6px 10px",
                  fontSize: 12, color: ch.effort === "Low" ? "#166534" : ch.effort === "Med" ? "#854d0e" : "#991b1b",
                  fontWeight: 600, textAlign: "center",
                }}>{ch.effort}</div>
                <div style={{
                  background: "rgba(74,122,181,0.15)",
                  borderRadius: 6, padding: "6px 6px",
                  fontSize: 12, color: "#2d5a8e", fontWeight: 700, textAlign: "center",
                }}>{ch.rank}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Marketing Strategy Timeline */}
      <div style={card}>
        <h2 style={{ fontSize: 17, fontWeight: 700, color: "#0d2137", margin: "0 0 16px" }}>
          Marketing Strategy — 3 Phase Timeline
        </h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14 }}>
          {PHASES.map((phase) => (
            <div key={phase.label} style={{
              background: phase.color,
              borderRadius: 12,
              padding: "16px",
              display: "flex",
              flexDirection: "column",
              gap: 8,
            }}>
              <div style={{
                background: "rgba(255,255,255,0.18)",
                borderRadius: 7,
                padding: "8px 12px",
                fontSize: 15,
                fontWeight: 700,
                color: "#fff",
                textAlign: "center",
              }}>
                {phase.label}
              </div>
              {phase.actions.map((a, i) => (
                <div key={i} style={{
                  background: "rgba(255,255,255,0.12)",
                  borderRadius: 7,
                  padding: "7px 12px",
                  fontSize: 12,
                  color: "rgb(255,255,255)",
                  lineHeight: 1.4,
                }}>
                  {a}
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
