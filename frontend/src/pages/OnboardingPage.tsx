import { useState } from "react"
import { useNavigate } from "react-router-dom"
import Logo from "@/components/Logo"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { saveOnboarding, type OnboardingInput } from "@/api/auth"

const INITIAL_FORM: OnboardingInput = {
  website: "",
  industry: "",
  description: "",
  ideal_customer: "",
  three_month_goal: "",
  previous_attempts: "",
  current_channels: "",
}

const STEPS = [
  {
    title: "Tell us about the business",
    description: "This gives every GrowthPilot agent the same company context.",
  },
  {
    title: "Who is your ideal customer?",
    description: "A concise ICP is enough. You can refine it later.",
  },
  {
    title: "What are you trying to achieve?",
    description: "Share the most important outcome for the next three months.",
  },
  {
    title: "What have you tried already?",
    description: "Past experiments and current channels help us avoid generic advice.",
  },
]

export default function OnboardingPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState(0)
  const [form, setForm] = useState(INITIAL_FORM)
  const [error, setError] = useState("")
  const [isSaving, setIsSaving] = useState(false)

  function update(key: keyof OnboardingInput, value: string) {
    setForm((current) => ({ ...current, [key]: value }))
    setError("")
  }

  async function finish() {
    setError("")
    setIsSaving(true)
    try {
      await saveOnboarding(form)
      navigate("/dashboard", { replace: true })
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Onboarding could not be saved.")
    } finally {
      setIsSaving(false)
    }
  }

  function next() {
    if (step < STEPS.length - 1) setStep((current) => current + 1)
    else void finish()
  }

  return (
    <main className="onboarding-page">
      <section className="onboarding-card" aria-labelledby="onboarding-title">
        <div className="onboarding-brand"><Logo size={34} /><span>GrowthPilot</span></div>
        <div className="onboarding-progress" aria-label={`Step ${step + 1} of ${STEPS.length}`}>
          {STEPS.map((_, index) => <span key={index} className={index <= step ? "active" : ""} />)}
        </div>
        <p className="onboarding-kicker">STEP {step + 1} OF {STEPS.length}</p>
        <h1 id="onboarding-title">{STEPS[step].title}</h1>
        <p className="onboarding-description">{STEPS[step].description}</p>

        <div className="onboarding-fields">
          {step === 0 && <>
            <label>Website<Input value={form.website} onChange={(event) => update("website", event.target.value)} placeholder="https://example.com" /></label>
            <label>Industry<Input value={form.industry} onChange={(event) => update("industry", event.target.value)} placeholder="B2B SaaS" /></label>
            <label>One-line description<Textarea value={form.description} onChange={(event) => update("description", event.target.value)} placeholder="What does your company help customers do?" /></label>
          </>}
          {step === 1 && <label>Ideal customer<Textarea autoFocus value={form.ideal_customer} onChange={(event) => update("ideal_customer", event.target.value)} placeholder="Bootstrapped B2B SaaS founders with 3–15 customers…" /></label>}
          {step === 2 && <label>Three-month goal<Textarea autoFocus value={form.three_month_goal} onChange={(event) => update("three_month_goal", event.target.value)} placeholder="Reach £10k MRR and validate our best acquisition channel…" /></label>}
          {step === 3 && <>
            <label>What worked or did not work?<Textarea autoFocus value={form.previous_attempts} onChange={(event) => update("previous_attempts", event.target.value)} placeholder="LinkedIn founder stories worked; broad cold email did not…" /></label>
            <label>Current channels<Input value={form.current_channels} onChange={(event) => update("current_channels", event.target.value)} placeholder="LinkedIn, Reddit, email" /></label>
          </>}
        </div>

        {error && <div className="form-error" role="alert">{error}</div>}
        <div className="onboarding-actions">
          <Button type="button" variant="outline" disabled={step === 0 || isSaving} onClick={() => setStep((current) => current - 1)}>Back</Button>
          <button className="skip-button" type="button" disabled={isSaving} onClick={next}>Skip for now</button>
          <Button type="button" disabled={isSaving} onClick={next}>{isSaving ? "Saving…" : step === STEPS.length - 1 ? "Finish" : "Continue"}</Button>
        </div>
      </section>
    </main>
  )
}
