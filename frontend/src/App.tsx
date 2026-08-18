import { useEffect, useState, type ReactNode } from "react"
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom"
import LandingPage from "@/pages/LandingPage"
import LoginPage from "@/pages/LoginPage"
import SignUpPage from "@/pages/SignUpPage"
import OnboardingPage from "@/pages/OnboardingPage"
import DashboardLayout from "@/pages/dashboard/DashboardLayout"
import DashboardHome from "@/pages/dashboard/DashboardHome"
import MarketResearch from "@/pages/dashboard/MarketResearch"
import GrowthGraph from "@/pages/dashboard/GrowthGraph"
import GTMStrategy from "@/pages/dashboard/GTMStrategy"
import ContentCreation from "@/pages/dashboard/ContentCreation"
import AIPartner from "@/pages/dashboard/AIPartner"
import AgentActivity from "@/pages/dashboard/AgentActivity"
import { ApiError } from "@/api/client"
import { getCurrentCompany } from "@/api/auth"

function RequireSession({ children }: { children: ReactNode }) {
  const location = useLocation()
  const [state, setState] = useState<"checking" | "ready" | "anonymous" | "error">("checking")

  useEffect(() => {
    let active = true
    getCurrentCompany()
      .then(() => active && setState("ready"))
      .catch((error) => {
        if (!active) return
        setState(error instanceof ApiError && error.status === 401 ? "anonymous" : "error")
      })
    return () => { active = false }
  }, [location.pathname])

  if (state === "checking") return <main className="session-state">Opening your GrowthPilot workspace…</main>
  if (state === "anonymous") return <Navigate to="/login" replace state={{ from: location.pathname }} />
  if (state === "error") return <main className="session-state" role="alert">We could not verify your session. Refresh the page or sign in again.</main>
  return children
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignUpPage />} />
        <Route path="/onboarding" element={<RequireSession><OnboardingPage /></RequireSession>} />
        <Route path="/dashboard" element={<RequireSession><DashboardLayout /></RequireSession>}>
          <Route index element={<DashboardHome />} />
          <Route path="market" element={<MarketResearch />} />
          <Route path="growthgraph" element={<GrowthGraph />} />
          <Route path="gtm" element={<GTMStrategy />} />
          <Route path="content" element={<ContentCreation />} />
          <Route path="ai-partner" element={<AIPartner />} />
          <Route path="activity" element={<AgentActivity />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
