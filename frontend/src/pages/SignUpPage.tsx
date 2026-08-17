import { useState } from "react"
import { useNavigate } from "react-router-dom"
import Logo from "@/components/Logo"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

export default function SignUpPage() {
  const navigate = useNavigate()
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    navigate("/dashboard")
  }

  return (
    <div style={{
      minHeight: "100vh",
      backgroundImage: `linear-gradient(to bottom, rgba(13,30,65,0.42) 0%, rgba(22,52,108,0.22) 50%, rgba(13,30,65,0.38) 100%), url(https://images.unsplash.com/photo-1511747779856-fd751a79aa22?w=3840&q=100&fit=crop&auto=format)`,
      backgroundSize: "cover",
      backgroundPosition: "center center",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      fontFamily: "'Oranienbaum', serif",
      padding: 24,
    }}>
      <div style={{
        background: "rgba(255,255,255,0.55)",
        backdropFilter: "blur(12px)",
        border: "1.5px solid rgba(255,255,255,0.7)",
        borderRadius: 24,
        padding: "48px 44px",
        width: "100%",
        maxWidth: 440,
        boxShadow: "0 8px 40px rgba(13,33,55,0.12)",
      }}>
        {/* Logo + Brand */}
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 32 }}>
          <Logo size={36} />
          <span style={{
            fontFamily: "'Lobster Two', cursive",
            fontWeight: 700,
            fontSize: 37,
            color: "#0d2137",
          }}>
            GrowthPilot
          </span>
        </div>

        <h1 style={{
          fontFamily: "'Playfair Display', serif",
          fontSize: 28,
          fontWeight: 700,
          color: "#0d2137",
          margin: "0 0 6px",
        }}>
          Create your account
        </h1>
        <p style={{ fontFamily: "'Oranienbaum', serif", fontSize: 14, color: "#2d5a8e", margin: "0 0 28px" }}>
          Join 1,200+ founders using GrowthPilot to grow smarter.
        </p>

        <div style={{
          borderTop: "1px solid rgba(74,122,181,0.2)",
          margin: "0 0 24px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}>
          <span style={{ fontSize: 11, letterSpacing: "0.1em", color: "#4a7ab5", padding: "0 12px", marginTop: -10, fontWeight: 600, textTransform: "uppercase" }}>
            form
          </span>
        </div>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 18 }}>
          <div>
            <label style={{ fontFamily: "'Oranienbaum', serif", fontSize: 17, fontWeight: 600, color: "#0d2137", display: "block", marginBottom: 6 }}>
              Full Name
            </label>
            <Input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="Jane Smith"
              required
            />
          </div>
          <div>
            <label style={{ fontFamily: "'Oranienbaum', serif", fontSize: 17, fontWeight: 600, color: "#0d2137", display: "block", marginBottom: 6 }}>
              Email
            </label>
            <Input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="you@company.com"
              required
            />
          </div>
          <div>
            <label style={{ fontFamily: "'Oranienbaum', serif", fontSize: 17, fontWeight: 600, color: "#0d2137", display: "block", marginBottom: 6 }}>
              Password
            </label>
            <Input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>

          <Button
            type="submit"
            style={{ marginTop: 4 }}
          >
            [ Create Account ]
          </Button>

          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => navigate("/login")}
            style={{ fontSize: 17, padding: "11px" }}
          >
            Already have one? Sign in →
          </Button>
        </form>
      </div>
    </div>
  )
}
