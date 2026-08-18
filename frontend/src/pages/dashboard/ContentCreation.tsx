import { useState } from "react"
import { useLocation } from "react-router-dom"
import { generateContent, type MemoryHit } from "@/api/chat"
import MemoryInspector from "@/components/MemoryInspector"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"

const CONTENT_TABS = ["LinkedIn Post", "X Thread", "Email Campaign", "Landing Page Copy"]

function emptyContent() {
  return Object.fromEntries(CONTENT_TABS.map((tab) => [tab, ""])) as Record<string, string>
}

export default function ContentCreation() {
  const location = useLocation()
  const navigationPrompt = (location.state as { prompt?: unknown } | null)?.prompt
  const [activeTab, setActiveTab] = useState("LinkedIn Post")
  const [copied, setCopied] = useState(false)
  const [prompt, setPrompt] = useState(typeof navigationPrompt === "string" ? navigationPrompt : "")
  const [contentByTab, setContentByTab] = useState(emptyContent)
  const [memoriesByTab, setMemoriesByTab] = useState<Record<string, MemoryHit[]>>({})
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState("")

  async function handleCopy() {
    const content = contentByTab[activeTab]
    if (!content) return
    await navigator.clipboard.writeText(content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  async function handleGenerate() {
    if (isGenerating) return
    setError("")
    setIsGenerating(true)
    try {
      const request = prompt.trim() || `Create a ${activeTab} using the company's saved strategy, audience, research, and campaign reflections.`
      const result = await generateContent(request)
      setContentByTab((current) => ({ ...current, [activeTab]: result.content }))
      setMemoriesByTab((current) => ({ ...current, [activeTab]: result.memories }))
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Content generation failed.")
    } finally {
      setIsGenerating(false)
    }
  }

  return <section className="content-live-page" aria-labelledby="content-heading">
    <header className="dashboard-page-heading">
      <div>
        <p className="dashboard-kicker">CONTENT AGENT OUTPUT</p>
        <h1 id="content-heading">Content Creation</h1>
      </div>
      <span className="connection-badge">● Live Content Agent</span>
    </header>

    <div className="content-prompt-card">
      <label htmlFor="content-prompt">What should GrowthPilot create?</label>
      <div>
        <Input id="content-prompt" value={prompt} onChange={(event) => setPrompt(event.target.value)} placeholder="A LinkedIn post using our latest campaign reflection…" />
        <button disabled={isGenerating} type="button" onClick={() => void handleGenerate()}>{isGenerating ? "Generating…" : "Generate with AI"}</button>
      </div>
      {error && <div className="form-error" role="alert">{error}</div>}
    </div>

    <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
      <TabsList className="mb-[20px]">
        {CONTENT_TABS.map((tab) => <TabsTrigger key={tab} value={tab}>{tab}</TabsTrigger>)}
      </TabsList>

      {CONTENT_TABS.map((tab) => {
        const memories = memoriesByTab[tab] || []
        const reflectionMemories = memories.filter((memory) => memory.memory_type === "reflection")
        const content = contentByTab[tab]
        return <TabsContent key={tab} value={tab}>
          <article className="content-output-card">
            <header>
              <div>
                <p className="dashboard-kicker">LIVE OUTPUT</p>
                <h2>{tab}</h2>
              </div>
              <div>
                <button disabled={isGenerating} type="button" onClick={() => void handleGenerate()}>{isGenerating ? "Generating…" : "Regenerate"}</button>
                <button disabled={!content} type="button" onClick={() => void handleCopy()}>{copied ? "Copied!" : "Copy"}</button>
              </div>
            </header>

            {reflectionMemories.length > 0 && <MemoryInspector
              memories={reflectionMemories}
              label={`Based on ${reflectionMemories.length} reflection ${reflectionMemories.length === 1 ? "memory" : "memories"}`}
            />}
            {memories.length > reflectionMemories.length && <MemoryInspector
              memories={memories.filter((memory) => memory.memory_type !== "reflection")}
              label={`Plus ${memories.length - reflectionMemories.length} supporting ${memories.length - reflectionMemories.length === 1 ? "memory" : "memories"}`}
            />}

            {content ? <Textarea value={content} onChange={(event) => setContentByTab((current) => ({ ...current, [tab]: event.target.value }))} /> : <div className="content-empty-output">
              <strong>No generated {tab.toLowerCase()} yet.</strong>
              <span>Run the Content Agent above. The result and its actual memory provenance will appear here.</span>
            </div>}
          </article>
        </TabsContent>
      })}
    </Tabs>
  </section>
}
