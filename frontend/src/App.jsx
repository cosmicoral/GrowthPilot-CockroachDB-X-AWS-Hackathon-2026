import { useEffect, useState } from "react";
import {
  BrowserRouter,
  Link,
  Navigate,
  Route,
  Routes,
  useNavigate,
} from "react-router-dom";

import {
  ApiError,
  getCurrentCompany,
  login,
  logout,
  signup,
} from "./api/auth";

const EMPTY_FORM = {
  name: "",
  email: "",
  password: "",
};

function chatDestination() {
  return import.meta.env.VITE_CHAT_URL?.trim() || "/chat";
}

function goToChat() {
  window.location.replace(chatDestination());
}

function usesLocalChatRoute() {
  const configuredDestination = import.meta.env.VITE_CHAT_URL?.trim();
  return !configuredDestination || configuredDestination === "/chat";
}

function maskEmail(email) {
  if (typeof email !== "string") {
    return "***";
  }

  const [localPart, domain] = email.split("@");
  if (!localPart || !domain) {
    return "***";
  }

  const visibleEnd = localPart.length > 1 ? localPart.at(-1) : "";
  return `${localPart[0]}***${visibleEnd}@${domain}`;
}

function BrandLogo() {
  return (
    <div className="brand-logo" aria-label="GrowthPilot">
      <span aria-hidden="true" className="brand-symbol">
        ◢
      </span>
      <span>GrowthPilot</span>
    </div>
  );
}

function PageFrame({ children }) {
  return (
    <main className="auth-page">
      {children}
      <button
        aria-label="Help"
        className="help-button"
        title="Help"
        type="button"
      >
        ?
      </button>
    </main>
  );
}

function AuthPage({ mode }) {
  const isSignup = mode === "signup";
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    // Auto-forwarding is safe only for our local /chat route because it uses
    // the same session check below. An independently deployed chat can apply
    // different checks and redirect back here, so auto-forwarding to an
    // external VITE_CHAT_URL could otherwise create a redirect loop.
    if (!usesLocalChatRoute()) {
      return undefined;
    }

    let isActive = true;

    getCurrentCompany()
      .then(() => {
        if (isActive) {
          goToChat();
        }
      })
      .catch(() => {
        // A missing or expired session is expected on an authentication page.
      });

    return () => {
      isActive = false;
    };
  }, []);

  function updateField(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
    if (error) {
      setError("");
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      if (isSignup) {
        await signup({
          name: form.name.trim(),
          email: form.email.trim(),
          password: form.password,
        });
      } else {
        await login({
          email: form.email.trim(),
          password: form.password,
        });
      }

      // The server keeps the opaque session in an HttpOnly cookie. No token is
      // read or persisted by browser JavaScript.
      goToChat();
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Something went wrong. Please try again.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <PageFrame>
      <section
        aria-labelledby="auth-heading"
        aria-busy={isSubmitting}
        className={`auth-card${isSignup ? " signup-card" : ""}`}
      >
        <BrandLogo />

        <header className="auth-header">
          <h1 id="auth-heading">
            {isSignup ? "Create your account" : "Welcome back"}
          </h1>
          <p>
            {isSignup
              ? "Join GrowthPilot and start growing."
              : "Sign in to your GrowthPilot account to continue."}
          </p>
        </header>

        <div aria-hidden="true" className="form-divider">
          <span>FORM</span>
        </div>

        <form onSubmit={handleSubmit}>
          {isSignup && (
            <label>
              Company name
              <input
                autoComplete="organization"
                disabled={isSubmitting}
                maxLength={200}
                name="name"
                onChange={updateField}
                placeholder="Your company"
                required
                type="text"
                value={form.name}
              />
            </label>
          )}

          <label>
            Email
            <input
              autoComplete="email"
              disabled={isSubmitting}
              name="email"
              onChange={updateField}
              placeholder="you@company.com"
              required
              type="email"
              value={form.email}
            />
          </label>

          <label>
            Password
            <input
              autoComplete={isSignup ? "new-password" : "current-password"}
              disabled={isSubmitting}
              maxLength={128}
              minLength={isSignup ? 8 : 1}
              name="password"
              onChange={updateField}
              placeholder="••••••••"
              required
              type="password"
              value={form.password}
            />
          </label>

          {error && (
            <div aria-live="polite" className="form-error" role="alert">
              {error}
            </div>
          )}

          <button
            className="submit-button"
            disabled={isSubmitting}
            type="submit"
          >
            {isSubmitting
              ? "[ Please wait… ]"
              : isSignup
                ? "[ Create Account ]"
                : "[ Sign In ]"}
          </button>
        </form>

        <Link className="auth-switch" to={isSignup ? "/login" : "/signup"}>
          {isSignup
            ? "Already have an account? Sign in →"
            : "No account? Sign up →"}
        </Link>
      </section>
    </PageFrame>
  );
}

function SessionPage() {
  const navigate = useNavigate();
  const [company, setCompany] = useState(null);
  const [error, setError] = useState("");
  const [isSigningOut, setIsSigningOut] = useState(false);

  useEffect(() => {
    let isActive = true;

    getCurrentCompany()
      .then((profile) => {
        if (isActive) {
          setCompany(profile);
        }
      })
      .catch((requestError) => {
        if (!isActive) {
          return;
        }
        if (requestError instanceof ApiError && requestError.status === 401) {
          navigate("/login", { replace: true });
          return;
        }
        setError(requestError.message || "We could not load your workspace.");
      });

    return () => {
      isActive = false;
    };
  }, [navigate]);

  async function handleLogout() {
    setError("");
    setIsSigningOut(true);
    try {
      await logout();
      navigate("/login", { replace: true });
    } catch (requestError) {
      setError(requestError.message || "We could not sign you out. Please try again.");
      setIsSigningOut(false);
    }
  }

  return (
    <PageFrame>
      <section aria-live="polite" className="auth-card session-card">
        <BrandLogo />
        <header className="auth-header session-header">
          <p className="session-kicker">SESSION ACTIVE</p>
          <h1>{company ? `Welcome, ${company.name}` : "Opening your workspace…"}</h1>
          <p>
            {company
              ? "Your secure GrowthPilot session is ready for the chat workspace."
              : "We are checking your secure session."}
          </p>
        </header>

        {company && (
          <div className="session-profile">
            <span>Signed in as</span>
            <strong title="Email address hidden for privacy">
              {maskEmail(company.email)}
            </strong>
          </div>
        )}

        {error && (
          <div className="form-error" role="alert">
            {error}
          </div>
        )}

        {company && (
          <button
            className="submit-button"
            disabled={isSigningOut}
            onClick={handleLogout}
            type="button"
          >
            {isSigningOut ? "[ Signing out… ]" : "[ Sign Out ]"}
          </button>
        )}
      </section>
    </PageFrame>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AuthPage mode="login" />} path="/login" />
        <Route element={<AuthPage mode="signup" />} path="/signup" />
        <Route element={<SessionPage />} path="/chat" />
        <Route element={<Navigate replace to="/login" />} path="/" />
        <Route element={<Navigate replace to="/login" />} path="*" />
      </Routes>
    </BrowserRouter>
  );
}
