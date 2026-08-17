import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import LandingPage from "@/pages/LandingPage"
import LoginPage from "@/pages/LoginPage"
import SignUpPage from "@/pages/SignUpPage"
import DashboardLayout from "@/pages/dashboard/DashboardLayout"
import DashboardHome from "@/pages/dashboard/DashboardHome"
import MarketResearch from "@/pages/dashboard/MarketResearch"
import GTMStrategy from "@/pages/dashboard/GTMStrategy"
import ContentCreation from "@/pages/dashboard/ContentCreation"
import AIPartner from "@/pages/dashboard/AIPartner"

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignUpPage />} />
        <Route path="/dashboard" element={<DashboardLayout />}>
          <Route index element={<DashboardHome />} />
          <Route path="market" element={<MarketResearch />} />
          <Route path="gtm" element={<GTMStrategy />} />
          <Route path="content" element={<ContentCreation />} />
          <Route path="ai-partner" element={<AIPartner />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
