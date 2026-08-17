import { useState, useRef, useEffect } from "react"
import Logo from "@/components/Logo"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"

interface Message {
  role: "ai" | "user"
  text: string
}

interface Memory {
  text: string
  score: number
  age: string
  source: "user" | "system" | "reflection"
}

const MEMORIES: Memory[] = [
  { text: "Semantic Reddit drove the most signups at launch", score: 0.87, age: "3 weeks ago", source: "system" },
  { text: "[user] prefers LinkedIn over Twitter for B2B outreach", score: 0.71, age: "2 months ago", source: "user" },
  { text: "Primary ICP: bootstrapped B2B SaaS founders, 0–5 employees, pre-PMF", score: 0.94, age: "1 week ago", source: "system" },
  { text: "Goal: reach $10K MRR by end of Q4 2026", score: 0.82, age: "3 weeks ago", source: "user" },
  { text: "Biggest competitor concern is StrategyAI's pricing model undercutting positioning", score: 0.68, age: "5 weeks ago", source: "system" },
  { text: "Founder story posts on Friday consistently outperform other content formats", score: 0.76, age: "6 weeks ago", source: "system" },
  { text: "Engineering workflow posts generate 2.8× more engagement than AI automation lists — hypothesis from simulated analytics", score: 0.91, age: "just now", source: "reflection" },
]

const INITIAL_MESSAGES: Message[] = [
  {
    role: "ai",
    text: "Hi! I'm your GrowthPilot AI Partner. I have full context on your business — your market position, ICP, competitors, GTM strategy, and content goals. Ask me anything about your positioning, messaging, market dynamics, or next growth moves. What's on your mind?",
  },
]

const QUICK_SUGGESTIONS = [
  "How should I refine my ICP?",
  "What's my strongest differentiator?",
  "Write me a cold email opener",
  "What should I post about this week?",
]

const AI_RESPONSES: Record<string, string> = {
  "How should I refine my ICP?": `Great question. Based on your market research data, your highest-converting segment is bootstrapped B2B SaaS founders with 0–5 employees who are pre-product-market-fit and actively doing founder-led sales.

To sharpen this further, I'd recommend adding two filters:
1. **Stage filter**: Founders who have 3–15 paying customers but feel stuck scaling beyond that cohort. That "first 10 to 100" moment is your sweet spot.
2. **Pain filter**: Focus on those who describe their positioning as "unclear" or who've been rejected by investors for "not knowing their ICP."

Would you like me to rewrite your positioning statement with this tighter ICP?`,

  "What's my strongest differentiator?": `Looking at your competitor analysis, here's what stands out:

Your three closest competitors — Competitor.io, GrowBase, and StrategyAI — all offer either market data OR content generation, but none combine both with strategic context.

**Your strongest differentiator is context-aware strategy.** You're not just generating content or pulling market data — you're connecting them through a business-aware AI that understands the *why* behind every decision.

The phrase I'd use: "GrowthPilot doesn't just give you tools — it gives you a co-pilot that thinks with you."

Want me to integrate this into your positioning statement?`,

  "Write me a cold email opener": `Here are three openers worth testing, ordered from most to least aggressive:

**Option A (Pain-led):**
"{{first_name}} — most founders I talk to know their product cold, but struggle to explain why a specific buyer should choose them over funded alternatives. That gap costs deals. Worth 15 minutes?"

**Option B (Insight-led):**
"{{first_name}} — we analyzed 200 early-stage SaaS positioning statements last quarter. The ones that converted best had one thing in common: they named a specific moment of frustration, not a feature. Thought it might be useful context given what you're building."

**Option C (Direct):**
"{{first_name}} — you're building [Company]. I think your positioning could close 30% more deals. Here's why, and what I'd change."

Which one fits your tone best? I can write the full sequence from there.`,

  "What should I post about this week?": `Based on your content calendar gaps and trending signals in your market, here are three high-leverage LinkedIn post ideas for this week:

**Post 1 (Monday — Insight):**
The counterintuitive truth about product-market fit: it's not about the product. Share the positioning angle — founders who nail "why us" before "what we do" grow 2.4× faster.

**Post 2 (Wednesday — Framework):**
"5 questions that expose a broken GTM strategy" — a carousel post that gets founders to self-diagnose. High share potential.

**Post 3 (Friday — Story):**
A brief story about a founder who pivoted their ICP (not their product) and 3×'d conversion. Real-feeling, emotional, relatable.

Want me to draft the full copy for any of these?`,
}

function scoreColor(score: number) {
  if (score >= 0.85) return "#2d8a4e"
  if (score >= 0.75) return "#4a7ab5"
  if (score >= 0.65) return "#8a6e2d"
  return "#8a3a2d"
}

export default function AIPartner() {
  const [messages, setMessages] = useState<Message[]>(INITIAL_MESSAGES)
  const [input, setInput] = useState("")
  const [memoryOpen, setMemoryOpen] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const sendMessage = (text: string) => {
    if (!text.trim()) return
    const userMsg: Message = { role: "user", text }
    const aiResponse = AI_RESPONSES[text] || `That's a great question about "${text.substring(0, 40)}..." Let me analyze your business context and get back to you with a tailored answer based on your market position, ICP, and current GTM strategy.`
    setMessages(prev => [...prev, userMsg, { role: "ai", text: aiResponse }])
    setInput("")
  }

  return (
    <div style={{ fontFamily: "'Oranienbaum', serif", display: "flex", flexDirection: "column", height: "calc(100vh - 180px)", minHeight: 500 }}>
      <h1 style={{
        fontFamily: "'Playfair Display', serif",
        fontSize: 28,
        fontWeight: 700,
        color: "#0d2137",
        margin: "0 0 20px",
        background: "rgba(74,122,181,0.15)",
        display: "inline-block",
        padding: "6px 16px",
        borderRadius: 8,
        flexShrink: 0,
      }}>
        AI Partner
      </h1>

      {/* Main area: chat + memory panel side by side */}
      <div style={{ flex: 1, display: "flex", gap: 14, minHeight: 0 }}>

        {/* Chat column */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
          {/* Chat window */}
          <div style={{
            flex: 1,
            background: "rgba(255,255,255,0.5)",
            border: "1.5px solid rgba(255,255,255,0.65)",
            borderRadius: 16,
            padding: "20px",
            backdropFilter: "blur(6px)",
            overflowY: "auto",
            marginBottom: 14,
            display: "flex",
            flexDirection: "column",
            gap: 14,
          }}>
            {messages.map((msg, i) => (
              <div
                key={i}
                style={{
                  display: "flex",
                  gap: 12,
                  flexDirection: msg.role === "user" ? "row-reverse" : "row",
                  alignItems: "flex-start",
                }}
              >
                {msg.role === "ai" ? (
                  <div style={{
                    width: 32, height: 32, borderRadius: "50%",
                    background: "#4a7ab5",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    flexShrink: 0,
                  }}>
                    <Logo size={22} />
                  </div>
                ) : (
                  <div style={{
                    width: 32, height: 32, borderRadius: "50%",
                    background: "#0d2137", color: "#fff",
                    fontWeight: 700, fontSize: 12,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    flexShrink: 0,
                  }}>
                    JS
                  </div>
                )}
                <div style={{ display: "flex", flexDirection: "column", gap: 6, maxWidth: "72%" }}>
                  <div style={{
                    background: msg.role === "ai" ? "rgba(74,122,181,0.1)" : "rgba(13,33,55,0.85)",
                    border: msg.role === "ai" ? "1px solid rgba(74,122,181,0.2)" : "none",
                    borderRadius: msg.role === "ai" ? "4px 14px 14px 14px" : "14px 4px 14px 14px",
                    padding: "12px 16px",
                    fontSize: 15,
                    lineHeight: 1.6,
                    color: msg.role === "ai" ? "#0d2137" : "#fff",
                    whiteSpace: "pre-wrap",
                  }}>
                    {msg.text}
                  </div>
                  {/* Memory pill — only on AI messages that aren't the greeting */}
                  {msg.role === "ai" && i > 0 && (
                    <button
                      onClick={() => setMemoryOpen(o => !o)}
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: 6,
                        alignSelf: "flex-start",
                        background: memoryOpen ? "rgba(74,122,181,0.16)" : "rgba(255,255,255,0.55)",
                        border: "1px solid rgba(74,122,181,0.25)",
                        borderRadius: 20,
                        padding: "4px 11px 4px 8px",
                        fontFamily: "'Oranienbaum', serif",
                        fontSize: 12,
                        color: "#2d5a8e",
                        cursor: "pointer",
                        transition: "all 0.18s",
                        backdropFilter: "blur(4px)",
                      }}
                      onMouseEnter={e => (e.currentTarget.style.background = "rgba(74,122,181,0.22)")}
                      onMouseLeave={e => (e.currentTarget.style.background = memoryOpen ? "rgba(74,122,181,0.16)" : "rgba(255,255,255,0.55)")}
                    >
                      <span style={{ fontSize: 13 }}>🧠</span>
                      Answered using <strong style={{ color: "#0d2137" }}>7 memories</strong> · oldest 3 weeks ago
                    </button>
                  )}
                </div>
              </div>
            ))}
            <div ref={bottomRef} />
          </div>

          {/* Quick suggestions */}
          <div style={{ display: "flex", gap: 8, marginBottom: 10, flexWrap: "wrap", flexShrink: 0 }}>
            {QUICK_SUGGESTIONS.map(s => (
              <button
                key={s}
                onClick={() => sendMessage(s)}
                style={{
                  background: "rgba(255,255,255,0.45)",
                  border: "1px solid rgba(255,255,255,0.6)",
                  color: "#2d5a8e",
                  borderRadius: 20,
                  padding: "6px 14px",
                  fontFamily: "'Oranienbaum', serif",
                  fontWeight: 500,
                  fontSize: 15,
                  cursor: "pointer",
                  transition: "all 0.2s",
                  backdropFilter: "blur(4px)",
                }}
                onMouseEnter={e => { e.currentTarget.style.background = "rgba(255,255,255,0.7)"; e.currentTarget.style.color = "#0d2137" }}
                onMouseLeave={e => { e.currentTarget.style.background = "rgba(255,255,255,0.45)"; e.currentTarget.style.color = "#2d5a8e" }}
              >
                {s}
              </button>
            ))}
          </div>

          {/* Input bar */}
          <div style={{
            display: "flex",
            gap: 10,
            background: "rgba(255,255,255,0.5)",
            border: "1.5px dashed rgba(74,122,181,0.35)",
            borderRadius: 12,
            padding: "8px 8px 8px 16px",
            backdropFilter: "blur(6px)",
            flexShrink: 0,
          }}>
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && sendMessage(input)}
              placeholder="Type a question or ask anything about your market, strategy, content..."
              style={{
                flex: 1,
                background: "none",
                border: "none",
                outline: "none",
                fontFamily: "'Oranienbaum', serif",
                fontSize: 13,
                color: "#0d2137",
              }}
            />
            <button
              onClick={() => sendMessage(input)}
              style={{
                background: "#0d2137",
                border: "none",
                color: "#fff",
                borderRadius: 8,
                padding: "8px 18px",
                fontFamily: "'Oranienbaum', serif",
                fontWeight: 700,
                fontSize: 13,
                cursor: "pointer",
                transition: "background 0.2s",
              }}
              onMouseEnter={e => (e.currentTarget.style.background = "#1a3a5c")}
              onMouseLeave={e => (e.currentTarget.style.background = "#0d2137")}
            >
              Send
            </button>
          </div>
        </div>

        {/* Memory Inspector panel */}
        <div style={{
          width: memoryOpen ? 320 : 0,
          minWidth: memoryOpen ? 320 : 0,
          overflow: "hidden",
          transition: "width 0.28s cubic-bezier(0.4,0,0.2,1), min-width 0.28s cubic-bezier(0.4,0,0.2,1)",
          flexShrink: 0,
        }}>
          <div style={{
            width: 320,
            height: "100%",
            display: "flex",
            flexDirection: "column",
            background: "rgba(255,255,255,0.52)",
            border: "1.5px solid rgba(255,255,255,0.68)",
            borderRadius: 16,
            backdropFilter: "blur(10px)",
            overflow: "hidden",
          }}>
            {/* Panel header */}
            <div style={{
              padding: "16px 18px 14px",
              borderBottom: "1px solid rgba(74,122,181,0.14)",
              flexShrink: 0,
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                <span style={{ fontSize: 15 }}>🧠</span>
                <span style={{
                  fontFamily: "'Playfair Display', serif",
                  fontWeight: 700,
                  fontSize: 14,
                  color: "#0d2137",
                }}>Memory Context</span>
              </div>
              <p style={{
                margin: 0,
                fontFamily: "'Oranienbaum', serif",
                fontSize: 13,
                color: "#4a7ab5",
                lineHeight: 1.4,
              }}>
                Answered using <strong style={{ color: "#0d2137" }}>7 memories</strong> from your history
              </p>
            </div>

            {/* Memory rows — using shadcn ScrollArea */}
            <ScrollArea className="flex-1">
              <div style={{ padding: "10px 0" }}>
                {MEMORIES.map((mem, i) => (
                  <div
                    key={i}
                    style={{
                      padding: "11px 18px",
                      borderBottom: i < MEMORIES.length - 1 ? "1px solid rgba(74,122,181,0.08)" : "none",
                      transition: "background 0.15s",
                      cursor: "default",
                    }}
                    onMouseEnter={e => (e.currentTarget.style.background = "rgba(74,122,181,0.07)")}
                    onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
                  >
                    {/* Score + age row */}
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 5 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                        {/* Score bar */}
                        <div style={{
                          width: 36,
                          height: 4,
                          borderRadius: 2,
                          background: "rgba(74,122,181,0.15)",
                          overflow: "hidden",
                        }}>
                          <div style={{
                            width: `${mem.score * 100}%`,
                            height: "100%",
                            background: scoreColor(mem.score),
                            borderRadius: 2,
                            transition: "width 0.4s ease",
                          }} />
                        </div>
                        <span style={{
                          fontFamily: "'Oranienbaum', serif",
                          fontSize: 12,
                          fontWeight: 700,
                          color: scoreColor(mem.score),
                          letterSpacing: "0.02em",
                        }}>{mem.score.toFixed(2)}</span>
                      </div>
                      <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
                        {/* shadcn Badge for memory source */}
                        {mem.source === "user" && (
                          <Badge variant="user">you</Badge>
                        )}
                        {mem.source === "reflection" && (
                          <Badge variant="reflection">reflection</Badge>
                        )}
                        <span style={{
                          fontFamily: "'Oranienbaum', serif",
                          fontSize: 12,
                          color: "#8aa8c8",
                          whiteSpace: "nowrap",
                        }}>{mem.age}</span>
                      </div>
                    </div>
                    {/* Memory text */}
                    <p style={{
                      margin: 0,
                      fontFamily: "'Oranienbaum', serif",
                      fontSize: 13,
                      color: "#1a3a5c",
                      lineHeight: 1.45,
                    }}>{mem.text}</p>
                  </div>
                ))}
              </div>
            </ScrollArea>

            {/* Panel footer */}
            <div style={{
              padding: "10px 18px",
              borderTop: "1px solid rgba(74,122,181,0.1)",
              flexShrink: 0,
            }}>
              <p style={{
                margin: 0,
                fontFamily: "'Oranienbaum', serif",
                fontSize: 12,
                color: "#8aa8c8",
                textAlign: "center",
              }}>
                Scored by semantic similarity · updated live
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
