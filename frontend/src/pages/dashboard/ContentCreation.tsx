import { useState } from "react"
import { useLocation } from "react-router-dom"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { generateContent } from "@/api/chat"
import type { MemoryHit } from "@/api/chat"
import MemoryInspector from "@/components/MemoryInspector"

const CONTENT_TABS = ["LinkedIn Post", "X Thread", "Email Campaign", "Landing Page Copy"]

const CONTENT_SAMPLES: Record<string, string> = {
  "LinkedIn Post": `🧭 Most founders I talk to have a GTM problem disguised as a product problem.

They ship features. They build roadmaps. But they never answer the foundational question:

"Who exactly is this for, and why should they choose us over the alternative?"

That's not a marketing question. It's a strategy question.

At GrowthPilot, we've worked with 1,200+ founders on this exact challenge. Here's what we've found:

The companies that crack positioning early grow 2–3× faster — not because they have better products, but because every team member, investor, and prospect instantly understands the value.

Positioning isn't your tagline. It's the lens through which every decision gets made.

If you're pre-Series A and still haven't nailed your ICP, drop a comment or DM me. Happy to share what's working.

#StartupGrowth #GTM #B2BSaaS #Positioning #FounderLed`,

  "X Thread": `1/ Most early-stage SaaS companies don't have a marketing problem.

They have a positioning problem.

Here's a 5-step framework that's helped 1,200+ founders get clarity: 🧵

2/ Step 1: Name your ICP with surgical precision.

Not "SMBs in tech." Try: "Bootstrapped B2B SaaS founders, 0–2 employees, pre-product-market-fit, doing founder-led sales."

The more specific, the better your messaging converts.

3/ Step 2: Find the moment of frustration.

What happens 5 minutes before your best customer decides to look for a solution like yours?

That moment is your positioning anchor.

4/ Step 3: Write a positioning statement, not a tagline.

Format: For [ICP] who [need], [Brand] is the [category] that [benefit] — unlike [alternatives].

It sounds corporate. It works brilliantly.

5/ Step 4: Run it through your team.

Ask 5 people: "Who is this for?" If they give 5 different answers, your positioning isn't done yet.

6/ Step 5: Let it bleed into every channel.

Website, cold email, investor decks, onboarding — all of it should reflect one clear POV.

Consistency beats cleverness every time.

/end — follow for weekly GTM frameworks for founders.`,

  "Email Campaign": `Subject: The 1 question that separates fast-growing SaaS from the rest

Hi {{first_name}},

Quick question for you:

If a new prospect landed on your website right now and had 8 seconds to decide whether to keep reading — would your positioning make the cut?

For most early-stage founders, the honest answer is "probably not."

That's not a knock on your product. It's a clarity problem — and it's fixable.

At GrowthPilot, we built an entire platform around helping founders like you answer the foundational questions:
→ Who is your ICP, really?
→ What makes you different from well-funded alternatives?
→ What messaging converts — not just sounds good?

We've helped 1,200+ founders build positioning-led GTM strategies that turn confused visitors into confident buyers.

This week only, new accounts get a 30-day free trial on our Growth plan (normally $79/mo).

→ [Start your free trial]

No credit card required. Full platform access from day one.

Best,
The GrowthPilot Team

P.S. Reply to this email if you want to hop on a 20-min strategy call. We do 10 per week, first-come first-served.`,

  "Landing Page Copy": `HEADLINE:
Stop Guessing. Start Growing.

SUBHEADLINE:
GrowthPilot is the AI-powered co-pilot that gives early-stage founders a clear positioning, a battle-tested GTM strategy, and content that actually converts — all in one place.

[CTA: Start free for 30 days →]

——

SECTION: The Problem

You're building something real. But without a clear ICP, differentiated positioning, and a systematic content engine, growth feels like shouting into the void.

Generic AI tools generate words. GrowthPilot generates strategy.

——

SECTION: How It Works

1. Define your market
We help you map competitors, identify customer pain points, and surface the insights that matter — automatically updated every week.

2. Build your GTM playbook
Get a positioning statement, customer personas, ranked launch channels, and a 3-phase go-to-market timeline — tailored to your business.

3. Create content that converts
Generate LinkedIn posts, email sequences, and landing copy in your voice — grounded in your actual strategy, not templates.

4. Ask your AI Partner anything
Get real-time strategic advice, messaging feedback, or market analysis. GrowthPilot has full context on your business.

——

TESTIMONIALS:

"I had my positioning statement, ICP, and first GTM playbook ready in 2 hours. That would've taken me 2 months alone." — Sarah M., Founder

"The market research alone is worth 10× the price. I cancelled two research subscriptions the day I signed up." — James R., CEO`,
}

export default function ContentCreation() {
  const location = useLocation()
  const navigationPrompt = (location.state as { prompt?: unknown } | null)?.prompt
  const [activeTab, setActiveTab] = useState("LinkedIn Post")
  const [copied, setCopied] = useState(false)
  const [prompt, setPrompt] = useState(
    typeof navigationPrompt === "string" ? navigationPrompt : "",
  )
  const [contentByTab, setContentByTab] = useState(CONTENT_SAMPLES)
  const [memoriesByTab, setMemoriesByTab] = useState<Record<string, MemoryHit[]>>({})
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState("")

  const handleCopy = () => {
    navigator.clipboard.writeText(contentByTab[activeTab])
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  async function handleGenerate() {
    setError("")
    setIsGenerating(true)
    try {
      const request = prompt.trim() || `Create a ${activeTab} using the company's saved strategy, audience, and previous campaign memories.`
      const result = await generateContent(request)
      setContentByTab((current) => ({ ...current, [activeTab]: result.content }))
      setMemoriesByTab((current) => ({ ...current, [activeTab]: result.memories }))
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Content generation failed.")
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div style={{ fontFamily: "'Oranienbaum', serif" }}>
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
      }}>
        Content Creation
      </h1>

      <div className="content-prompt-card">
        <label htmlFor="content-prompt">What should GrowthPilot create?</label>
        <div>
          <Input id="content-prompt" value={prompt} onChange={(event) => setPrompt(event.target.value)} placeholder="A LinkedIn post about our strongest positioning insight…" />
          <button disabled={isGenerating} type="button" onClick={() => void handleGenerate()}>{isGenerating ? "Generating…" : "Generate with AI"}</button>
        </div>
        {error && <div className="form-error" role="alert">{error}</div>}
      </div>

      {/* shadcn Tabs — styled to match existing tab buttons exactly */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="mb-[20px]">
          {CONTENT_TABS.map(tab => (
            <TabsTrigger key={tab} value={tab}>
              {tab}
            </TabsTrigger>
          ))}
        </TabsList>

        {CONTENT_TABS.map(tab => {
          const reflectionMemories = (memoriesByTab[tab] || []).filter(
            (memory) => memory.memory_type === "reflection",
          )

          return <TabsContent key={tab} value={tab}>
            {/* Content card */}
            <div style={{
              background: "rgba(255,255,255,0.5)",
              border: "1.5px solid rgba(255,255,255,0.65)",
              borderRadius: 16,
              padding: "20px 24px",
              backdropFilter: "blur(6px)",
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: tab === "LinkedIn Post" ? 10 : 16 }}>
                <h2 style={{ fontSize: 17, fontWeight: 700, color: "#0d2137", margin: 0 }}>
                  Generated Content — {tab}
                </h2>
                <div style={{ display: "flex", gap: 8 }}>
                  <button
                    disabled={isGenerating}
                    onClick={() => void handleGenerate()}
                    style={{
                      background: "rgba(74,122,181,0.12)",
                      border: "1px solid rgba(74,122,181,0.25)",
                      color: "#2d5a8e",
                      borderRadius: 6,
                      padding: "6px 14px",
                      fontFamily: "'Oranienbaum', serif",
                      fontWeight: 600,
                      fontSize: 15,
                      cursor: "pointer",
                      transition: "background 0.2s",
                    }}
                    onMouseEnter={e => (e.currentTarget.style.background = "rgba(74,122,181,0.22)")}
                    onMouseLeave={e => (e.currentTarget.style.background = "rgba(74,122,181,0.12)")}
                  >
                    {isGenerating ? "[ Generating… ]" : "[ Regenerate ]"}
                  </button>
                  <button
                    onClick={handleCopy}
                    style={{
                      background: copied ? "rgba(34,197,94,0.15)" : "rgba(74,122,181,0.12)",
                      border: `1px solid ${copied ? "rgba(34,197,94,0.3)" : "rgba(74,122,181,0.25)"}`,
                      color: copied ? "#166534" : "#2d5a8e",
                      borderRadius: 6,
                      padding: "6px 14px",
                      fontFamily: "'Oranienbaum', serif",
                      fontWeight: 600,
                      fontSize: 15,
                      cursor: "pointer",
                      transition: "all 0.2s",
                    }}
                  >
                    {copied ? "Copied!" : "[ Copy ]"}
                  </button>
                </div>
              </div>

              {tab === "LinkedIn Post" && (
                <div style={{ marginBottom: 14 }}>
                  {reflectionMemories.length > 0 ? (
                    <MemoryInspector
                      memories={reflectionMemories}
                      label={`Based on ${reflectionMemories.length} reflection ${reflectionMemories.length === 1 ? "memory" : "memories"}`}
                    />
                  ) : (
                    <Badge variant="memoryTag">
                      🧠 Generate to see the memories actually used
                    </Badge>
                  )}
                </div>
              )}

              {/* shadcn Textarea — styled to match existing exactly */}
              <Textarea
                value={contentByTab[tab]}
                onChange={(event) => setContentByTab((current) => ({ ...current, [tab]: event.target.value }))}
              />
            </div>
          </TabsContent>
        })}
      </Tabs>
    </div>
  )
}
