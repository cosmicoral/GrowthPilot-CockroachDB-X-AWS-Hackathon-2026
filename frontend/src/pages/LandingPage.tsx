import { useState } from "react"
import { useNavigate } from "react-router-dom"
import Logo from "@/components/Logo"

const HERO_IMAGES = [
  { url: "https://images.unsplash.com/photo-1617761141732-d481912af1a9?w=400&h=300&fit=crop&auto=format&q=50", fallback: "#1a3a5c" },
  { url: "https://images.unsplash.com/photo-1579445505461-acecf2596190?w=400&h=300&fit=crop&auto=format&q=50", fallback: "#0f2840" },
  { url: "https://images.unsplash.com/photo-1692797960717-1738a7a872c8?w=400&h=300&fit=crop&auto=format&q=50", fallback: "#162d47" },
  { url: "https://images.unsplash.com/photo-1723047579305-6cbaeb915f2a?w=400&h=300&fit=crop&auto=format&q=50", fallback: "#1a3a5c" },
  { url: "https://images.unsplash.com/photo-1594655151913-93647a6d998e?w=400&h=300&fit=crop&auto=format&q=50", fallback: "#0f2840" },
  { url: "https://images.unsplash.com/photo-1717565813196-8944b57877f8?w=400&h=300&fit=crop&auto=format&q=50", fallback: "#162d47" },
]

const PRICING_PLANS = [
  {
    name: "Starter",
    description: "Perfect for founders just getting started",
    monthly: 29,
    annual: 19,
    features: ["Market snapshot reports", "5 content pieces/mo", "Basic GTM framework", "Email support"],
    highlight: false,
    cta: "Get Started",
  },
  {
    name: "Growth",
    star: true,
    description: "For teams ready to accelerate",
    monthly: 79,
    annual: 59,
    features: ["Full market research suite", "Unlimited content", "GTM playbooks", "AI Partner access"],
    highlight: true,
    cta: "Most Popular",
  },
  {
    name: "Scale",
    description: "For growing businesses with real traction",
    monthly: 149,
    annual: 109,
    features: ["Multi-brand workspace", "Custom personas", "Priority AI insights", "Slack integration"],
    highlight: false,
    cta: "Get Started",
  },
  {
    name: "Enterprise",
    description: "For orgs that need full control",
    monthly: 349,
    annual: 279,
    features: ["Dedicated success manager", "Custom AI training", "SSO + SCIM", "SLA guarantee"],
    highlight: false,
    cta: "Get Started",
  },
]

const FEATURES = [
  {
    icon: "🧭",
    heading: "Strategic Clarity",
    description: "Get a crystal-clear positioning statement and ICP profile grounded in real market data — not guesswork.",
  },
  {
    icon: "📡",
    heading: "Market Intelligence",
    description: "Monitor competitors, Reddit signals, and customer pain points in one live dashboard updated weekly.",
  },
  {
    icon: "✍️",
    heading: "Content at Scale",
    description: "Generate LinkedIn posts, email sequences, and landing copy that sounds like you, not a robot.",
  },
  {
    icon: "🤖",
    heading: "Your AI Partner",
    description: "Ask anything about your strategy, market, or messaging. GrowthPilot has full context on your business.",
  },
]

export default function LandingPage() {
  const navigate = useNavigate()
  const [billing, setBilling] = useState<"monthly" | "annual">("monthly")

  return (
    <div style={{ fontFamily: "'Oranienbaum', serif", backgroundColor: "#b8d4f0", minHeight: "100vh" }}>

      {/* ───── SEGMENT 1: HERO ───── */}
      <section style={{ height: "100vh", position: "relative", overflow: "hidden" }}>
        {/* Hero background image */}
        <div style={{
          position: "absolute",
          inset: 0,
          backgroundImage: "url(/hero-bg.jpg)",
          backgroundSize: "cover",
          backgroundPosition: "center",
          backgroundColor: "#1a3a5c",
        }} />
        {/* Dark overlay */}
        <div style={{
          position: "absolute",
          inset: 0,
          background: "linear-gradient(135deg, rgba(13,33,55,0.72) 0%, rgba(13,33,55,0.45) 50%, rgba(13,33,55,0.55) 100%)",
          color: "rgb(65, 131, 203)",
        }} />

        {/* Top-left: Logo */}
        <div style={{ position: "absolute", top: 24, left: 28 }}>
          <Logo size={44} />
        </div>

        {/* Top-right: Login + Sign Up floating bar */}
        <div style={{
          position: "absolute",
          top: 20,
          right: 28,
          display: "flex",
          alignItems: "center",
          gap: 0,
          padding: 4,
          background: "rgba(13,33,55,0.62)",
          border: "1px solid rgba(255,255,255,0.3)",
          borderRadius: 12,
          backdropFilter: "blur(14px)",
          boxShadow: "0 10px 28px rgba(5, 16, 29, 0.2)",
        }}>
          <button
            onClick={() => navigate("/login")}
            style={{
              background: "transparent",
              border: "none",
              color: "#fff",
              borderRadius: 8,
              padding: "10px 18px",
              fontFamily: "'Oranienbaum', serif",
              fontWeight: 500,
              fontSize: 16,
              cursor: "pointer",
              transition: "all 0.2s",
            }}
            onMouseEnter={e => (e.currentTarget.style.background = "rgba(255,255,255,0.12)")}
            onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
          >
            login
          </button>
          <button
            onClick={() => navigate("/signup")}
            style={{
              background: "transparent",
              border: "none",
              borderLeft: "1px solid rgba(255,255,255,0.28)",
              color: "#fff",
              borderRadius: 8,
              padding: "10px 18px",
              fontFamily: "'Oranienbaum', serif",
              fontWeight: 600,
              fontSize: 16,
              cursor: "pointer",
              transition: "all 0.2s",
            }}
            onMouseEnter={e => (e.currentTarget.style.background = "rgba(255,255,255,0.12)")}
            onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
          >
            signup
          </button>
        </div>

        {/* Center-left: Brand name + CTA */}
        <div className="hero-content" style={{
          position: "absolute",
          top: "45%",
          transform: "translateY(-50%)",
          left: 46,
          maxWidth: 900,
          zIndex: 5,
        }}>
          <h1 className="hero-title" style={{
            fontFamily: "'Lobster Two', cursive",
            fontSize: "clamp(54px, 11.5vw, 165px)",
            fontWeight: 700,
            color: "#ffffff",
            margin: "0 0 28px 0",
            lineHeight: 0.96,
            letterSpacing: "-1.5px",
            textShadow: "0 7px 34px rgba(0,0,0,0.45)",
          }}>
            GrowthPilot
          </h1>
          <div style={{ display: "flex", gap: 12 }}>
            <button
              onClick={() => navigate("/signup")}
              style={{
                background: "rgba(255, 255, 255, 0.19)",
                border: "1.5px solid rgba(255, 255, 255, 0.4)",
                color: "#ffffff",
                borderRadius: 13,
                padding: "16px 40px",
                fontFamily: "'Playfair Display SC', serif",
                fontWeight: 600,
                fontSize: 26,
                letterSpacing: "2.2px",
                cursor: "pointer",
                backdropFilter: "blur(16px)",
                boxShadow: "0 11px 30px rgba(0, 0, 0, 0.32)",
                transition: "all 0.2s ease",
              }}
              onMouseEnter={e => {
                e.currentTarget.style.background = "rgba(255, 255, 255, 0.31)"
                e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.7)"
                e.currentTarget.style.transform = "translateY(-2px)"
              }}
              onMouseLeave={e => {
                e.currentTarget.style.background = "rgba(255, 255, 255, 0.19)"
                e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.4)"
                e.currentTarget.style.transform = "translateY(0)"
              }}
            >
              START FOR FREE →
            </button>
          </div>
        </div>
      </section>

      {/* ───── SEGMENT 2: PRICING ───── */}
      <section style={{
        padding: "0 40px 80px",
        overflow: "hidden",
        backgroundImage: `linear-gradient(to bottom, rgba(13,30,65,0.38) 0%, rgba(22,52,108,0.22) 50%, rgba(13,30,65,0.32) 100%), url(https://images.unsplash.com/photo-1511747779856-fd751a79aa22?w=3840&q=100&fit=crop&auto=format)`,
        backgroundSize: "cover",
        backgroundPosition: "center center",
        backgroundAttachment: "fixed",
      }}>
        {/* Curved quote panel */}
        <div style={{ textAlign: "center", marginBottom: 56, position: "relative" }}>
          <div style={{
            height: 176,
            margin: "0 -40px 24px",
            position: "relative",
            display: "flex",
            justifyContent: "center",
            overflow: "hidden",
          }}>
            <div style={{
              position: "absolute",
              top: -78,
              left: "50%",
              width: "min(760px, 102vw)",
              height: 250,
              transform: "translateX(-50%)",
              background: "#eff4ff",
              borderRadius: "50%",
            }} />
            <p style={{
              position: "relative",
              zIndex: 1,
              margin: "58px 20px 0",
              maxWidth: 620,
              alignSelf: "flex-start",
              fontFamily: "'Playfair Display', serif",
              fontSize: "clamp(21px, 2.2vw, 28px)",
              fontWeight: 700,
              lineHeight: 1.02,
              letterSpacing: "-0.045em",
              color: "#0d0d13",
            }}>
              A memory-aware AI partner for positioning, messaging, and growth.
            </p>
          </div>

          <p style={{
            fontFamily: "'Playfair Display SC', serif",
            fontSize: 60,
            fontWeight: 600,
            letterSpacing: "1px",
            lineHeight: "50px",
            textTransform: "uppercase",
            color: "rgb(233, 241, 249)",
            margin: "0 0 8px",
          }}>Pricing</p>
          <p style={{
            fontFamily: "'Lobster Two', cursive",
            color: "rgb(13, 18, 24)",
            margin: "0 0 28px",
            fontSize: 30,
          }}>
            No surprise fees. No lock-in. Cancel any time.
          </p>

          {/* Toggle */}
          <div style={{
            display: "inline-flex",
            background: "rgba(255,255,255,0.5)",
            borderRadius: 8,
            padding: 4,
            gap: 4,
          }}>
            {(["monthly", "annual"] as const).map(b => (
              <button
                key={b}
                onClick={() => setBilling(b)}
                style={{
                  background: billing === b ? "#0d2137" : "transparent",
                  color: billing === b ? "#fff" : "#2d5a8e",
                  border: "none",
                  borderRadius: 6,
                  padding: "8px 20px",
                  fontFamily: "'Playfair Display SC', serif",
                  fontWeight: 600,
                  fontSize: 14,
                  cursor: "pointer",
                  transition: "all 0.2s",
                  textTransform: "capitalize",
                }}
              >
                {b === "annual" ? "Annual (save 25%)" : "Monthly"}
              </button>
            ))}
          </div>
        </div>

        {/* 4 plan cards */}
        <div className="pricing-grid" style={{
          display: "grid",
          gridTemplateColumns: "repeat(4, 1fr)",
          gap: 16,
          maxWidth: 1100,
          margin: "0 auto",
        }}>
          {PRICING_PLANS.map((plan) => (
            <div
              key={plan.name}
              style={{
                background: plan.highlight ? "#0d2137" : "rgba(255,255,255,0.45)",
                border: plan.highlight ? "2px solid #4a7ab5" : "1.5px solid rgba(255,255,255,0.6)",
                borderRadius: 16,
                padding: "28px 22px",
                display: "flex",
                flexDirection: "column",
                gap: 0,
                backdropFilter: "blur(8px)",
                boxShadow: plan.highlight ? "0 8px 32px rgba(13,33,55,0.25)" : "0 2px 12px rgba(13,33,55,0.08)",
                transition: "transform 0.2s",
              }}
              onMouseEnter={e => (e.currentTarget.style.transform = "translateY(-4px)")}
              onMouseLeave={e => (e.currentTarget.style.transform = "translateY(0)")}
            >
              <div style={{ marginBottom: 6, fontFamily: "'Playfair Display SC', serif" }}>
                <span style={{
                  fontFamily: "'Playfair Display SC', serif",
                  fontWeight: 700,
                  fontSize: 16,
                  color: plan.highlight ? "#8ab4d8" : "#0d2137",
                }}>
                  {plan.name} {plan.star ? "★" : ""}
                </span>
              </div>
              <p style={{
                fontFamily: "'Playfair Display', serif",
                fontSize: 13,
                color: plan.highlight ? "#8ab4d8" : "#2d5a8e",
                margin: "0 0 14px",
                lineHeight: "25px",
              }}>
                {plan.description}
              </p>
              <div style={{
                background: plan.highlight ? "#4a7ab5" : "rgba(74,122,181,0.15)",
                borderRadius: 8,
                padding: "12px 16px",
                marginBottom: 18,
                textAlign: "center",
              }}>
                <span style={{
                  fontFamily: "'Playfair Display', serif",
                  fontSize: 32,
                  fontWeight: 700,
                  color: plan.highlight ? "#fff" : "#0d2137",
                }}>
                  ${billing === "monthly" ? plan.monthly : plan.annual}
                </span>
                <span style={{ fontSize: 13, color: plan.highlight ? "#c4daef" : "#4a7ab5", marginLeft: 4 }}>/ mo</span>
              </div>

              <div style={{ borderTop: `1px solid ${plan.highlight ? "rgba(255,255,255,0.12)" : "rgba(74,122,181,0.2)"}`, paddingTop: 14, marginBottom: 14 }}>
                <p style={{ fontSize: 11, fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: plan.highlight ? "#5b9bd5" : "#4a7ab5", marginBottom: 10 }}>features</p>
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {plan.features.map((f, i) => (
                    <div key={i} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span style={{
                        width: 16,
                        height: 16,
                        borderRadius: 4,
                        background: plan.highlight ? "#4a7ab5" : "rgba(74,122,181,0.2)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: 10,
                        color: plan.highlight ? "#fff" : "#4a7ab5",
                        flexShrink: 0,
                      }}>✓</span>
                      <span style={{ fontFamily: "'Oranienbaum', serif", fontSize: 15, color: plan.highlight ? "#d4e8f8" : "#1a3a5c" }}>{f}</span>
                    </div>
                  ))}
                </div>
              </div>

              <button
                onClick={() => navigate("/signup")}
                style={{
                  marginTop: "auto",
                  background: plan.highlight ? "#4a7ab5" : "transparent",
                  border: plan.highlight ? "none" : "1.5px solid #2d5a8e",
                  color: plan.highlight ? "#fff" : "#0d2137",
                  borderRadius: 8,
                  padding: "11px",
                  fontFamily: "'Oranienbaum', serif",
                  fontWeight: 600,
                  fontSize: 16,
                  cursor: "pointer",
                  transition: "all 0.2s",
                  width: "100%",
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.background = plan.highlight ? "#2d5a8e" : "rgba(13,33,55,0.08)"
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.background = plan.highlight ? "#4a7ab5" : "transparent"
                }}
              >
                {plan.cta}
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* ───── SEGMENT 3: WHY GROWTHPILOT IS DIFFERENT ───── */}
      <section style={{
        padding: "80px 40px",
        backgroundImage: `linear-gradient(to bottom, rgba(13,30,65,0.32) 0%, rgba(22,52,108,0.18) 50%, rgba(13,30,65,0.38) 100%), url(https://images.unsplash.com/photo-1511747779856-fd751a79aa22?w=3840&q=100&fit=crop&auto=format)`,
        backgroundSize: "cover",
        backgroundPosition: "center center",
        backgroundAttachment: "fixed",
      }}>
        <div style={{ maxWidth: 1100, margin: "0 auto" }}>
          <p style={{
            fontFamily: "'Playfair Display', serif",
            fontSize: 23,
            fontWeight: 700,
            letterSpacing: "2px",
            textTransform: "uppercase",
            color: "rgba(255,255,255,0.7)",
            margin: "0 0 8px",
          }}>What makes us unique</p>
          <h2 style={{
            fontFamily: "'Lobster Two', cursive",
            fontSize: "50px",
            fontWeight: 700,
            color: "#ffffff",
            lineHeight: "50px",
            margin: "0 0 36px",
          }}>
            why GrowthPilot is different
          </h2>

          {/* 4-col feature grid */}
          <div className="feature-grid" style={{
            display: "grid",
            gridTemplateColumns: "repeat(4, 1fr)",
            gap: 16,
            marginBottom: 32,
          }}>
            {FEATURES.map((f) => (
              <div
                key={f.heading}
                style={{
                  background: "rgba(74,122,181,0.7)",
                  borderRadius: 20,
                  padding: "28px 22px",
                  display: "flex",
                  flexDirection: "column",
                  gap: 12,
                  boxShadow: "0 4px 20px rgba(13,33,55,0.12)",
                  transition: "transform 0.2s",
                }}
                onMouseEnter={e => (e.currentTarget.style.transform = "translateY(-4px)")}
                onMouseLeave={e => (e.currentTarget.style.transform = "translateY(0)")}
              >
                <div style={{
                  width: 48,
                  height: 48,
                  background: "rgba(255,255,255,0.15)",
                  borderRadius: 12,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 22,
                }}>
                  {f.icon}
                </div>
                <h3 style={{
                  fontFamily: "'Playfair Display', serif",
                  fontWeight: 700,
                  fontSize: 15,
                  color: "#fff",
                  margin: 0,
                }}>
                  {f.heading}
                </h3>
                <p style={{
                  fontFamily: "'Oranienbaum', serif",
                  fontSize: 15,
                  color: "rgba(255,255,255,0.8)",
                  margin: 0,
                  lineHeight: 1.55,
                }}>
                  {f.description}
                </p>
              </div>
            ))}
          </div>

          {/* Bottom CTA bar */}
          <div style={{
            background: "rgba(255,255,255,0.35)",
            border: "1.5px solid rgba(255,255,255,0.5)",
            borderRadius: 16,
            padding: "24px 32px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            backdropFilter: "blur(8px)",
          }}>
            <div>
              <h3 style={{
                fontFamily: "'Playfair Display', serif",
                fontSize: 22,
                fontWeight: 700,
                color: "#ffffff",
                margin: "0 0 4px",
              }}>
                Ready to stop guessing and start growing?
              </h3>
              <p style={{ fontFamily: "'Playfair Display SC', serif", margin: 0, fontSize: 12, color: "rgba(255,255,255,0.7)" }}>
            Build your go-to-market strategy with an AI partner that remembers the context.
              </p>
            </div>
            <button
              onClick={() => navigate("/signup")}
              style={{
                background: "#0d2137",
                border: "none",
                color: "#fff",
                borderRadius: 8,
                padding: "14px 30px",
                fontFamily: "'Oranienbaum', serif",
                fontWeight: 700,
                fontSize: 15,
                cursor: "pointer",
                whiteSpace: "nowrap",
                letterSpacing: "1%",
                transition: "background 0.2s",
              }}
              onMouseEnter={e => (e.currentTarget.style.background = "#1a3a5c")}
              onMouseLeave={e => (e.currentTarget.style.background = "#0d2137")}
            >
              Get Started Free →
            </button>
          </div>
        </div>
      </section>

      {/* ───── FOOTER ───── */}
      <footer style={{
        background: "rgba(72,86,111,0.6)",
        backdropFilter: "blur(20px)",
        WebkitBackdropFilter: "blur(20px)",
        borderTop: "1px solid rgba(255,255,255,0.1)",
        padding: "36px 48px 28px",
      }}>
        <div className="footer-grid" style={{
          display: "grid",
          gridTemplateColumns: "1fr auto auto auto",
          alignItems: "start",
          gap: 40,
        }}>
          {/* Brand */}
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
              <Logo size={22} />
              <span style={{ fontFamily: "'Lobster Two', cursive", fontWeight: 700, fontSize: 18, color: "#fff" }}>
                GrowthPilot
              </span>
            </div>
            <p style={{ margin: 0, fontSize: 13, color: "rgba(255,255,255,0.5)", lineHeight: 1.6, maxWidth: 240 }}>
              AI-powered growth strategy for early-stage founders. Market research, GTM playbooks, and content — in one place.
            </p>
          </div>

          {/* Product */}
          <div>
            <p style={{ margin: "0 0 10px", fontSize: 11, fontWeight: 700, letterSpacing: "0.1em", color: "rgba(255,255,255,0.35)", textTransform: "uppercase" }}>Product</p>
            {["Market Research", "GTM Strategy", "Content Studio", "AI Partner"].map(l => (
              <p key={l} style={{ margin: "0 0 6px", fontSize: 13, color: "rgba(255,255,255,0.55)", cursor: "pointer" }}
                onMouseEnter={e => (e.currentTarget.style.color = "#fff")}
                onMouseLeave={e => (e.currentTarget.style.color = "rgba(255,255,255,0.55)")}
              >{l}</p>
            ))}
          </div>

          {/* Company */}
          <div>
            <p style={{ margin: "0 0 10px", fontSize: 11, fontWeight: 700, letterSpacing: "0.1em", color: "rgba(255,255,255,0.35)", textTransform: "uppercase" }}>Company</p>
            {["About", "Blog", "Careers", "Contact"].map(l => (
              <p key={l} style={{ margin: "0 0 6px", fontSize: 13, color: "rgba(255,255,255,0.55)", cursor: "pointer" }}
                onMouseEnter={e => (e.currentTarget.style.color = "#fff")}
                onMouseLeave={e => (e.currentTarget.style.color = "rgba(255,255,255,0.55)")}
              >{l}</p>
            ))}
          </div>

          {/* Legal */}
          <div>
            <p style={{ margin: "0 0 10px", fontSize: 11, fontWeight: 700, letterSpacing: "0.1em", color: "rgba(255,255,255,0.35)", textTransform: "uppercase" }}>Legal</p>
            {["Privacy Policy", "Terms of Service", "Security", "Cookies"].map(l => (
              <p key={l} style={{ margin: "0 0 6px", fontSize: 13, color: "rgba(255,255,255,0.55)", cursor: "pointer" }}
                onMouseEnter={e => (e.currentTarget.style.color = "#fff")}
                onMouseLeave={e => (e.currentTarget.style.color = "rgba(255,255,255,0.55)")}
              >{l}</p>
            ))}
          </div>
        </div>

        {/* Bottom rule */}
        <div style={{
          marginTop: 24,
          paddingTop: 18,
          borderTop: "1px solid rgba(255,255,255,0.1)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}>
          <p style={{ margin: 0, fontSize: 12, color: "rgba(255,255,255,0.3)" }}>
            © 2026 GrowthPilot, Inc. All rights reserved.
          </p>
          <div style={{ display: "flex", gap: 16 }}>
            {[
              { label: "X", path: "M4 4l8 8M12 4l-8 8" },
              { label: "LinkedIn", path: "M3 7h2v6H3zM4 5a1 1 0 110-2 1 1 0 010 2zM7 7h2v1s.5-1 2-1c1.5 0 2 1 2 2.5V13h-2v-3c0-.8-.3-1.5-1-1.5s-1 .7-1 1.5v3H7V7z" },
              { label: "GitHub", path: "M8 2a6 6 0 00-1.9 11.7c.3.05.4-.13.4-.29v-1.02c-1.67.36-2.02-.8-2.02-.8-.27-.7-.67-.88-.67-.88-.55-.37.04-.36.04-.36.6.04.92.62.92.62.54.92 1.41.66 1.76.5.05-.39.21-.66.38-.81-1.34-.15-2.75-.67-2.75-2.97 0-.66.23-1.2.62-1.62-.06-.15-.27-.77.06-1.6 0 0 .51-.16 1.67.62a5.8 5.8 0 013.04 0c1.16-.78 1.67-.62 1.67-.62.33.83.12 1.45.06 1.6.39.43.62.96.62 1.62 0 2.31-1.41 2.82-2.75 2.97.22.19.41.56.41 1.13v1.67c0 .16.1.35.4.29A6 6 0 008 2z" },
            ].map(icon => (
              <button key={icon.label} title={icon.label} style={{
                background: "rgba(255,255,255,0.08)",
                border: "1px solid rgba(255,255,255,0.12)",
                borderRadius: 8,
                width: 30,
                height: 30,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                cursor: "pointer",
                color: "rgba(255,255,255,0.4)",
                transition: "all 0.18s",
              }}
                onMouseEnter={e => { e.currentTarget.style.background = "rgba(255,255,255,0.15)"; e.currentTarget.style.color = "#fff" }}
                onMouseLeave={e => { e.currentTarget.style.background = "rgba(255,255,255,0.08)"; e.currentTarget.style.color = "rgba(255,255,255,0.4)" }}
              >
                <svg width="13" height="13" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d={icon.path} />
                </svg>
              </button>
            ))}
          </div>
        </div>
      </footer>
    </div>
  )
}
