import { useState, useRef, useEffect } from "react"
import { useNavigate, useLocation, Outlet } from "react-router-dom"
import Logo from "@/components/Logo"
import { getCurrentCompany, logout as logoutSession, type CompanyProfile } from "@/api/auth"

const NAV_ICONS: Record<string, React.JSX.Element> = {
  Market: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="1,11 5,6 9,9 15,3" />
      <polyline points="11,3 15,3 15,7" />
    </svg>
  ),
  GrowthGraph: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="3" cy="8" r="1.5" />
      <circle cx="8" cy="3" r="1.5" />
      <circle cx="13" cy="8" r="1.5" />
      <circle cx="8" cy="13" r="1.5" />
      <line x1="4.1" y1="6.9" x2="6.9" y2="4.1" />
      <line x1="9.1" y1="4.1" x2="11.9" y2="6.9" />
      <line x1="11.9" y1="9.1" x2="9.1" y2="11.9" />
      <line x1="6.9" y1="11.9" x2="4.1" y2="9.1" />
    </svg>
  ),
  GTM: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="8" cy="8" r="6.5" />
      <circle cx="8" cy="8" r="1" fill="currentColor" stroke="none" />
      <line x1="8" y1="1.5" x2="8" y2="3.5" />
      <line x1="8" y1="12.5" x2="8" y2="14.5" />
      <line x1="1.5" y1="8" x2="3.5" y2="8" />
      <line x1="12.5" y1="8" x2="14.5" y2="8" />
    </svg>
  ),
  Content: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="1.5" width="12" height="13" rx="1.5" />
      <line x1="5" y1="5" x2="11" y2="5" />
      <line x1="5" y1="8" x2="11" y2="8" />
      <line x1="5" y1="11" x2="8.5" y2="11" />
    </svg>
  ),
  "AI Partner": (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2 11.5C2 12.33 2.67 13 3.5 13H7l3 2.5V13h2.5c.83 0 1.5-.67 1.5-1.5v-7C14 3.67 13.33 3 12.5 3h-9C2.67 3 2 3.67 2 4.5v7z" />
      <line x1="5" y1="7" x2="5" y2="7" strokeWidth="2" strokeLinecap="round" />
      <line x1="8" y1="7" x2="8" y2="7" strokeWidth="2" strokeLinecap="round" />
      <line x1="11" y1="7" x2="11" y2="7" strokeWidth="2" strokeLinecap="round" />
    </svg>
  ),
}

const NAV_ITEMS = [
  { label: "Market", path: "/dashboard/market" },
  { label: "GrowthGraph", path: "/dashboard/growthgraph" },
  { label: "GTM", path: "/dashboard/gtm" },
  { label: "Content", path: "/dashboard/content" },
  { label: "AI Partner", path: "/dashboard/ai-partner" },
]

export default function DashboardLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const [avatarOpen, setAvatarOpen] = useState(false)
  const [navOpen, setNavOpen] = useState(true)
  const [footerVisible, setFooterVisible] = useState(false)
  const [company, setCompany] = useState<CompanyProfile | null>(null)
  const [sessionError, setSessionError] = useState("")
  const footerRef = useRef<HTMLElement>(null)

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => setFooterVisible(entry.isIntersecting),
      { threshold: 0.1 }
    )
    if (footerRef.current) observer.observe(footerRef.current)
    return () => observer.disconnect()
  }, [])

  useEffect(() => {
    let active = true
    getCurrentCompany()
      .then((profile) => active && setCompany(profile))
      .catch((error) => active && setSessionError(error instanceof Error ? error.message : "Profile unavailable"))
    return () => { active = false }
  }, [])

  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: "auto" })
  }, [location.pathname])

  async function handleLogout() {
    setSessionError("")
    try {
      await logoutSession()
      navigate("/login", { replace: true })
    } catch (error) {
      setSessionError(error instanceof Error ? error.message : "Sign out failed")
    }
  }

  const initials = company?.name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("") || "GP"

  const isHome = location.pathname === "/dashboard"

  return (
    <div style={{
      minHeight: "100vh",
      fontFamily: "'Oranienbaum', serif",
      display: "flex",
      flexDirection: "column",
      position: "relative",
    }}>
      {/* Sky background */}
      <div aria-hidden="true" style={{
        position: "fixed",
        inset: 0,
        zIndex: 0,
        pointerEvents: "none",
        backgroundColor: "rgba(239,244,255,0.8)",
        backgroundImage: `linear-gradient(to bottom, rgba(13,30,65,0.42) 0%, rgba(22,52,108,0.22) 50%, rgba(13,30,65,0.38) 100%), url(https://images.unsplash.com/photo-1511747779856-fd751a79aa22?w=3840&q=100&fit=crop&auto=format)`,
        backgroundSize: "cover",
        backgroundPosition: "center center",
        backgroundRepeat: "no-repeat",
      }} />

      {/* Z-index wrapper */}
      <div style={{ position: "relative", zIndex: 1, display: "flex", flexDirection: "column", flex: 1 }}>

        {/* ── Floating top header (unchanged) ── */}
        <header style={{
          background: "rgba(255,255,255,0.64)",
          backdropFilter: "blur(16px)",
          border: "1px solid rgba(255,255,255,0.82)",
          borderRadius: 18,
          padding: "12px 28px",
          margin: "14px 20px 0",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          position: "sticky",
          top: 14,
          zIndex: 50,
          boxShadow: "0 10px 28px rgba(45,90,142,0.14)",
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <button
              onClick={() => navigate("/dashboard")}
              style={{ background: "none", border: "none", cursor: "pointer", display: "flex", alignItems: "center", gap: 8 }}
            >
              <Logo size={32} />
              <span style={{ fontFamily: "'Lobster Two', cursive", fontWeight: 700, fontSize: 25, color: "#0d2137" }}>
                GrowthPilot
              </span>
            </button>
            {!isHome && (
              <button
                onClick={() => navigate("/dashboard")}
                style={{
                  background: "rgba(74,122,181,0.12)",
                  border: "1px solid rgba(74,122,181,0.25)",
                  color: "#2d5a8e",
                  borderRadius: 6,
                  padding: "4px 12px",
                  fontFamily: "'Oranienbaum', serif",
                  fontWeight: 500,
                  fontSize: 15,
                  cursor: "pointer",
                  transition: "background 0.2s",
                }}
                onMouseEnter={e => (e.currentTarget.style.background = "rgba(74,122,181,0.22)")}
                onMouseLeave={e => (e.currentTarget.style.background = "rgba(74,122,181,0.12)")}
              >[ Home ]</button>
            )}
          </div>

          {/* Avatar */}
          <div style={{ position: "relative" }}>
            <button
              onClick={() => setAvatarOpen(!avatarOpen)}
              style={{
                width: 36, height: 36, borderRadius: "50%",
                background: "#4a7ab5",
                border: "2px solid rgba(255,255,255,0.7)",
                color: "#fff", fontWeight: 700, fontSize: 14,
                cursor: "pointer",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontFamily: "'Oranienbaum', serif",
              }}
            >{initials}</button>
            {avatarOpen && (
              <div style={{
                position: "absolute", top: 44, right: 0,
                background: "rgba(255,255,255,0.9)",
                backdropFilter: "blur(12px)",
                border: "1px solid rgba(74,122,181,0.2)",
                borderRadius: 10, padding: "8px 0",
                minWidth: 160,
                boxShadow: "0 8px 24px rgba(13,33,55,0.12)",
                zIndex: 100,
              }}>
                <div style={{ padding: "8px 16px 10px", borderBottom: "1px solid rgba(74,122,181,0.12)" }}>
                  <p style={{ margin: 0, fontSize: 17, fontWeight: 700, color: "#0d2137" }}>{company?.name || "GrowthPilot workspace"}</p>
                  <p style={{ margin: 0, fontSize: 15, color: "#4a7ab5" }}>{company?.email || "Loading profile…"}</p>
                </div>
                <button
                  onClick={() => { setAvatarOpen(false); void handleLogout() }}
                  style={{ display: "block", width: "100%", background: "none", border: "none", padding: "9px 16px", textAlign: "left", fontSize: 15, color: "#0d2137", cursor: "pointer", fontFamily: "'Oranienbaum', serif" }}
                  onMouseEnter={e => (e.currentTarget.style.background = "rgba(74,122,181,0.08)")}
                  onMouseLeave={e => (e.currentTarget.style.background = "none")}
                >Sign out</button>
                {sessionError && <p role="alert" style={{ padding: "4px 16px", color: "#991b1b", fontSize: 13 }}>{sessionError}</p>}
              </div>
            )}
          </div>
        </header>

        {/* ── Page content ── */}
        <main className="dashboard-content" style={{
          flex: 1,
          padding: "28px 32px 80px",
          boxSizing: "border-box",
          minWidth: 0,
        }}>
          <Outlet context={{ company }} />
        </main>

        {/* ── Footer ── */}
        <footer ref={footerRef} style={{
          background: "rgba(13,21,37,0.72)",
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

            {/* Product links */}
            <div>
              <p style={{ margin: "0 0 10px", fontSize: 11, fontWeight: 700, letterSpacing: "0.1em", color: "rgba(255,255,255,0.35)", textTransform: "uppercase" }}>Product</p>
              {["Market Research", "GTM Strategy", "Content Studio", "AI Partner"].map(l => (
                <p key={l} style={{ margin: "0 0 6px", fontSize: 13, color: "rgba(255,255,255,0.55)", cursor: "pointer" }}
                  onMouseEnter={e => (e.currentTarget.style.color = "#fff")}
                  onMouseLeave={e => (e.currentTarget.style.color = "rgba(255,255,255,0.55)")}
                >{l}</p>
              ))}
            </div>

            {/* Company links */}
            <div>
              <p style={{ margin: "0 0 10px", fontSize: 11, fontWeight: 700, letterSpacing: "0.1em", color: "rgba(255,255,255,0.35)", textTransform: "uppercase" }}>Company</p>
              {["About", "Blog", "Careers", "Contact"].map(l => (
                <p key={l} style={{ margin: "0 0 6px", fontSize: 13, color: "rgba(255,255,255,0.55)", cursor: "pointer" }}
                  onMouseEnter={e => (e.currentTarget.style.color = "#fff")}
                  onMouseLeave={e => (e.currentTarget.style.color = "rgba(255,255,255,0.55)")}
                >{l}</p>
              ))}
            </div>

            {/* Legal links */}
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

        {/* ── Bottom nav bar ── */}
        <div style={{
          position: "fixed",
          bottom: 20,
          left: 24,
          right: 24,
          zIndex: 50,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 8,
          pointerEvents: "none",
          transform: footerVisible ? "translateY(120px)" : "translateY(0)",
          transition: "transform 0.4s cubic-bezier(0.4,0,0.2,1)",
        }}>
          {/* Collapsed trigger pill — always visible */}
          {!navOpen && (
            <button
              onClick={() => setNavOpen(true)}
              style={{
                pointerEvents: "all",
                display: "flex",
                alignItems: "center",
                gap: 6,
                background: "rgba(13,21,37,0.88)",
                backdropFilter: "blur(24px)",
                WebkitBackdropFilter: "blur(24px)",
                border: "1px solid rgba(255,255,255,0.12)",
                borderRadius: 999,
                padding: "8px 20px",
                color: "rgba(255,255,255,0.7)",
                fontSize: 13,
                fontFamily: "'Oranienbaum', serif",
                letterSpacing: "0.06em",
                cursor: "pointer",
                boxShadow: "0 8px 32px rgba(0,0,0,0.32)",
                transition: "all 0.2s ease",
              }}
              onMouseEnter={e => (e.currentTarget.style.color = "#fff")}
              onMouseLeave={e => (e.currentTarget.style.color = "rgba(255,255,255,0.7)")}
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round">
                <line x1="2" y1="4" x2="12" y2="4" />
                <line x1="2" y1="7" x2="12" y2="7" />
                <line x1="2" y1="10" x2="12" y2="10" />
              </svg>
              Navigation
            </button>
          )}

          {/* Full nav bar */}
          <nav style={{
            pointerEvents: "all",
            width: "100%",
            display: "flex",
            alignItems: "center",
            background: "rgba(71,84,111,0.82)",
            backdropFilter: "blur(24px)",
            WebkitBackdropFilter: "blur(24px)",
            border: "1px solid rgba(255,255,255,0.1)",
            borderRadius: 16,
            padding: "6px 8px",
            gap: 2,
            boxShadow: "0 16px 48px rgba(0,0,0,0.28), inset 0 1px 0 rgba(255,255,255,0.08)",
            overflow: "hidden",
            maxHeight: navOpen ? 80 : 0,
            opacity: navOpen ? 1 : 0,
            paddingTop: navOpen ? 6 : 0,
            paddingBottom: navOpen ? 6 : 0,
            transition: "max-height 0.32s cubic-bezier(0.4,0,0.2,1), opacity 0.24s ease, padding 0.24s ease",
          }}>
            {NAV_ITEMS.map(item => {
              const active = location.pathname.startsWith(item.path)
              return (
                <button
                  key={item.path}
                  className="dashboard-nav-item"
                  title={item.label}
                  onClick={() => navigate(item.path)}
                  style={{
                    flex: 1,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: 8,
                    padding: "11px 20px",
                    borderRadius: 11,
                    border: "none",
                    background: active ? "rgba(255,255,255,0.12)" : "transparent",
                    color: active ? "#ffffff" : "rgba(255,255,255,0.45)",
                    fontFamily: "'Oranienbaum', serif",
                    fontWeight: active ? 700 : 500,
                    fontSize: 14,
                    letterSpacing: "0.04em",
                    cursor: "pointer",
                    transition: "all 0.18s ease",
                    whiteSpace: "nowrap",
                    position: "relative",
                  }}
                  onMouseEnter={e => { if (!active) e.currentTarget.style.color = "rgba(255,255,255,0.78)" }}
                  onMouseLeave={e => { if (!active) e.currentTarget.style.color = "rgba(255,255,255,0.45)" }}
                >
                  <span style={{ opacity: active ? 1 : 0.7, display: "flex" }}>{NAV_ICONS[item.label]}</span>
                  <span className="dashboard-nav-label">{item.label}</span>
                  {active && (
                    <span style={{
                      position: "absolute",
                      bottom: 5,
                      left: "50%",
                      transform: "translateX(-50%)",
                      width: 18,
                      height: 2,
                      borderRadius: 2,
                      background: "#7aa8e0",
                    }} />
                  )}
                </button>
              )
            })}

            {/* Collapse button */}
            <button
              onClick={() => setNavOpen(false)}
              title="Collapse navigation"
              style={{
                flexShrink: 0,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                width: 34,
                height: 34,
                borderRadius: 9,
                border: "none",
                background: "transparent",
                color: "rgba(255,255,255,0.3)",
                cursor: "pointer",
                transition: "all 0.18s",
                marginLeft: 4,
              }}
              onMouseEnter={e => { e.currentTarget.style.background = "rgba(255,255,255,0.08)"; e.currentTarget.style.color = "rgba(255,255,255,0.7)" }}
              onMouseLeave={e => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = "rgba(255,255,255,0.3)" }}
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round">
                <polyline points="2,5 7,9 12,5" />
              </svg>
            </button>
          </nav>
        </div>
      </div>
    </div>
  )
}
