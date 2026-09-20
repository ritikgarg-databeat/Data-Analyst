"use client";

import type { AuthResponse } from "@data-analyst-lab/shared";
import {
  ArrowRight,
  BadgeCheck,
  BarChart3,
  BriefcaseBusiness,
  Check,
  ChevronRight,
  Eye,
  EyeOff,
  KeyRound,
  LoaderCircle,
  LockKeyhole,
  Mail,
  Sparkles,
  User,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  createContext,
  FormEvent,
  ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/features/auth/auth-provider";
import { apiClient, ApiError } from "@/lib/api-client";
import { cn } from "@/lib/utils";

export type LandingAuthMode = "login" | "signup";

interface LandingAuthContextValue {
  openAuth: (mode: LandingAuthMode) => void;
}

const LandingAuthContext = createContext<LandingAuthContextValue | null>(null);
const WORKSPACE_START_TIMEOUT_MS = 180_000;

function sleep(milliseconds: number) {
  return new Promise(resolve => window.setTimeout(resolve, milliseconds));
}

async function waitForWorkspace(): Promise<boolean> {
  const deadline = Date.now() + WORKSPACE_START_TIMEOUT_MS;
  while (Date.now() < deadline) {
    try {
      await apiClient.get("/health");
      return true;
    } catch {
      await sleep(3_000);
    }
  }
  return false;
}

const visionMetrics = [
  [BarChart3, "Progress", "Visible"],
  [BadgeCheck, "Practice", "Real"],
  [BriefcaseBusiness, "Outcome", "Career"],
] as const;

export function LandingAuthExperience({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<LandingAuthMode>("signup");

  const updateAddress = useCallback((nextMode: LandingAuthMode | null) => {
    const url = new URL(window.location.href);
    if (nextMode) url.searchParams.set("auth", nextMode);
    else url.searchParams.delete("auth");
    window.history.replaceState(null, "", `${url.pathname}${url.search}${url.hash}`);
  }, []);

  const openAuth = useCallback((nextMode: LandingAuthMode) => {
    setMode(nextMode);
    setOpen(true);
    updateAddress(nextMode);
  }, [updateAddress]);

  useEffect(() => {
    const requestedMode = new URLSearchParams(window.location.search).get("auth");
    if (requestedMode === "login" || requestedMode === "signup") {
      const timer = window.setTimeout(() => {
        setMode(requestedMode);
        setOpen(true);
      }, 0);
      return () => window.clearTimeout(timer);
    }
  }, []);

  useEffect(() => {
    if (typeof fetch === "function") {
      void fetch("/api/v1/health", { cache: "no-store" }).catch(() => undefined);
    }
  }, []);

  const setDialogOpen = useCallback((nextOpen: boolean) => {
    setOpen(nextOpen);
    if (!nextOpen) updateAddress(null);
  }, [updateAddress]);

  const value = useMemo(() => ({ openAuth }), [openAuth]);

  return (
    <LandingAuthContext.Provider value={value}>
      {children}
      <LandingAuthModal open={open} mode={mode} setMode={setMode} setOpen={setDialogOpen} />
    </LandingAuthContext.Provider>
  );
}

export function LandingAuthTrigger({
  mode,
  children,
  className,
  ariaLabel,
}: {
  mode: LandingAuthMode;
  children: ReactNode;
  className?: string;
  ariaLabel?: string;
}) {
  const context = useContext(LandingAuthContext);
  if (!context) throw new Error("LandingAuthTrigger must be used inside LandingAuthExperience");

  return (
    <button
      type="button"
      aria-label={ariaLabel}
      aria-haspopup="dialog"
      className={className}
      onClick={() => context.openAuth(mode)}
    >
      {children}
    </button>
  );
}

interface LandingAuthModalProps {
  open: boolean;
  mode: LandingAuthMode;
  setMode: (mode: LandingAuthMode) => void;
  setOpen: (open: boolean) => void;
}

function LandingAuthModal({ open, mode, setMode, setOpen }: LandingAuthModalProps) {
  const router = useRouter();
  const { setAuthenticatedUser } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [busy, setBusy] = useState(false);
  const [unlocking, setUnlocking] = useState(false);
  const [error, setError] = useState("");
  const [startupMessage, setStartupMessage] = useState("");
  const redirectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => () => {
    if (redirectTimer.current) clearTimeout(redirectTimer.current);
  }, []);

  function changeMode(nextMode: LandingAuthMode) {
    setMode(nextMode);
    setError("");
    setStartupMessage("");
    const url = new URL(window.location.href);
    url.searchParams.set("auth", nextMode);
    window.history.replaceState(null, "", `${url.pathname}${url.search}${url.hash}`);
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setStartupMessage("");

    try {
      const authenticate = () => mode === "login"
        ? apiClient.post<AuthResponse>("/auth/login", { email, password })
        : apiClient.post<AuthResponse>("/auth/signup", { name, email, password });
      let result: AuthResponse;
      try {
        result = await authenticate();
      } catch (reason) {
        const starting = reason instanceof ApiError && [0, 502, 503].includes(reason.status);
        if (!starting) throw reason;
        setStartupMessage("Starting your secure workspace. This can take a minute on the free service…");
        if (!await waitForWorkspace()) {
          throw new Error("Your workspace is taking longer than expected to start. Please try again shortly.");
        }
        setStartupMessage("Workspace ready. Signing you in…");
        result = await authenticate();
      }

      setAuthenticatedUser(result);
      setStartupMessage("");
      setUnlocking(true);
      const destination = result.user.must_change_password ? "/change-password" : "/dashboard";
      redirectTimer.current = setTimeout(() => router.replace(destination), 1650);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "We could not open your workspace.");
      setStartupMessage("");
      setBusy(false);
    }
  }

  const login = mode === "login";

  function handleOpenChange(nextOpen: boolean) {
    if (!nextOpen) {
      setBusy(false);
      setUnlocking(false);
      setError("");
      setStartupMessage("");
      setPassword("");
    }
    setOpen(nextOpen);
  }

  return (
    <Dialog open={open} onOpenChange={unlocking ? undefined : handleOpenChange}>
      <DialogContent
        size="xl"
        className="auth-dialog-shell max-h-[94dvh] max-w-5xl gap-0 overflow-y-auto border-white/12 bg-[#090b17] p-0 text-white shadow-[0_40px_140px_-25px_rgba(76,29,149,.75)] lg:overflow-hidden [&>[data-slot=dialog-close]]:top-4 [&>[data-slot=dialog-close]]:right-4 [&>[data-slot=dialog-close]]:z-50 [&>[data-slot=dialog-close]]:text-white sm:[&>[data-slot=dialog-close]]:top-5 sm:[&>[data-slot=dialog-close]]:right-5"
      >
        <DialogTitle className="sr-only">{login ? "Sign in to Data Lab" : "Create your Data Lab account"}</DialogTitle>
        <DialogDescription className="sr-only">
          {login ? "Continue to your private learning workspace." : "Start your private learning workspace."}
        </DialogDescription>

        <div className="grid min-h-0 lg:min-h-150 lg:grid-cols-[.92fr_1.08fr]">
          <section className="auth-vision-panel relative hidden overflow-hidden border-r border-white/8 p-9 lg:flex lg:flex-col">
            <div className="auth-portal-grid absolute inset-0 opacity-50" aria-hidden="true" />
            <div className="auth-orbit auth-orbit-one" aria-hidden="true" />
            <div className="auth-orbit auth-orbit-two" aria-hidden="true" />

            <div className="relative z-10 flex items-center gap-2.5 text-sm font-semibold">
              <span className="landing-logo flex size-9 items-center justify-center rounded-xl">
                <Sparkles className="size-4" aria-hidden="true" />
              </span>
              Data Lab
            </div>

            <div className="relative z-10 my-auto">
              <div className="mb-7 flex items-center gap-3 text-xs text-violet-200/75">
                <span className="h-px w-10 bg-violet-300/40" /> YOUR NEXT CHAPTER
              </div>
              <h2 className="max-w-sm text-4xl leading-[1.05] font-semibold tracking-[-0.04em]">
                The work you want starts with the skills you build today.
              </h2>
              <p className="mt-5 max-w-sm leading-7 text-white/48">
                Step into a workspace designed to turn consistent learning into visible, career-ready proof.
              </p>

              <div className="auth-career-path relative mt-10 h-40" aria-hidden="true">
                <svg viewBox="0 0 360 140" className="absolute inset-0 h-full w-full overflow-visible">
                  <defs>
                    <linearGradient id="career-path-gradient" x1="0" x2="1">
                      <stop offset="0" stopColor="#7c5cff" stopOpacity=".25" />
                      <stop offset=".55" stopColor="#d946ef" />
                      <stop offset="1" stopColor="#67e8f9" />
                    </linearGradient>
                  </defs>
                  <path className="auth-path-line" d="M8 122 C74 116 88 82 142 89 S225 72 248 43 S306 13 352 18" fill="none" stroke="url(#career-path-gradient)" strokeWidth="2" />
                  <circle cx="8" cy="122" r="5" fill="#7c5cff" />
                  <circle className="auth-path-pulse" cx="142" cy="89" r="5" fill="#d946ef" />
                  <circle cx="248" cy="43" r="5" fill="#a78bfa" />
                  <circle className="auth-path-pulse auth-path-pulse-late" cx="352" cy="18" r="6" fill="#67e8f9" />
                </svg>
                <span className="absolute bottom-0 left-0 text-[10px] text-white/38">START</span>
                <span className="absolute top-19 left-[34%] text-[10px] text-fuchsia-200/65">SKILLS</span>
                <span className="absolute top-6 left-[64%] text-[10px] text-violet-200/65">PROJECTS</span>
                <span className="absolute -top-3 right-0 text-[10px] text-cyan-200">CAREER READY</span>
              </div>
            </div>

            <div className="relative z-10 grid grid-cols-3 gap-2">
              {visionMetrics.map(([Icon, label, value]) => (
                <div key={String(label)} className="rounded-xl border border-white/8 bg-white/4 p-3">
                  <Icon className="size-3.5 text-violet-300" />
                  <p className="mt-3 text-[11px] font-medium">{String(value)}</p>
                  <p className="text-[9px] text-white/32">{String(label)}</p>
                </div>
              ))}
            </div>
          </section>

          <section className="relative flex min-w-0 flex-col justify-center px-4 py-6 min-[380px]:px-6 sm:p-10 lg:p-12">
            <div className="auth-form-glow absolute top-0 right-0 size-72" aria-hidden="true" />
            <div className="relative z-10 mx-auto w-full max-w-md">
              <div className="mb-7 grid w-full max-w-60 grid-cols-2 rounded-full border border-white/8 bg-white/4 p-1 sm:mb-8" role="tablist" aria-label="Authentication mode">
                <button type="button" role="tab" aria-selected={login} onClick={() => changeMode("login")} className={cn("rounded-full px-2 py-2 text-xs font-medium transition-all min-[380px]:px-4", login ? "bg-white text-[#0a0b13] shadow-lg" : "text-white/45 hover:text-white")}>Sign in</button>
                <button type="button" role="tab" aria-selected={!login} onClick={() => changeMode("signup")} className={cn("rounded-full px-2 py-2 text-xs font-medium transition-all min-[380px]:px-4", !login ? "bg-white text-[#0a0b13] shadow-lg" : "text-white/45 hover:text-white")}>Create account</button>
              </div>

              <p className="text-xs font-medium tracking-[.18em] text-violet-300 uppercase">
                {login ? "Welcome back" : "Your future workspace"}
              </p>
              <h2 className="mt-3 pr-6 text-2xl font-semibold tracking-[-0.035em] min-[380px]:text-3xl sm:pr-0 sm:text-4xl">
                {login ? "Continue your momentum." : "Open the door to what’s next."}
              </h2>
              <p className="mt-3 text-sm leading-6 text-white/45">
                {login
                  ? "Your progress, projects, and personal learning path are waiting."
                  : "Create one private place for your skills, practice, projects, and career growth."}
              </p>

              <form className="mt-8 space-y-4" onSubmit={submit}>
                {!login ? (
                  <label className="auth-field block">
                    <span className="mb-2 block text-xs font-medium text-white/65">Your name</span>
                    <span className="relative block">
                      <User className="pointer-events-none absolute top-1/2 left-4 size-4 -translate-y-1/2 text-white/30" aria-hidden="true" />
                      <Input className="auth-input h-12 rounded-xl border-white/10 bg-white/4 pl-11 text-white placeholder:text-white/22" autoComplete="name" required value={name} onChange={event => setName(event.target.value)} placeholder="Your full name" />
                    </span>
                  </label>
                ) : null}

                <label className="auth-field block">
                  <span className="mb-2 block text-xs font-medium text-white/65">Email address</span>
                  <span className="relative block">
                    <Mail className="pointer-events-none absolute top-1/2 left-4 size-4 -translate-y-1/2 text-white/30" aria-hidden="true" />
                    <Input className="auth-input h-12 rounded-xl border-white/10 bg-white/4 pl-11 text-white placeholder:text-white/22" type="email" autoComplete="email" required value={email} onChange={event => setEmail(event.target.value)} placeholder="you@example.com" />
                  </span>
                </label>

                <label className="auth-field block">
                  <span className="mb-2 flex items-center justify-between text-xs font-medium text-white/65">
                    Password
                    {login ? <Link href="/forgot-password" className="font-normal text-violet-300 transition hover:text-violet-200">Need help?</Link> : <span className="font-normal text-white/30">12–128 characters</span>}
                  </span>
                  <span className="relative block">
                    <KeyRound className="pointer-events-none absolute top-1/2 left-4 size-4 -translate-y-1/2 text-white/30" aria-hidden="true" />
                    <Input className="auth-input h-12 rounded-xl border-white/10 bg-white/4 pr-11 pl-11 text-white placeholder:text-white/22" type={showPassword ? "text" : "password"} autoComplete={login ? "current-password" : "new-password"} minLength={login ? undefined : 12} maxLength={128} required value={password} onChange={event => setPassword(event.target.value)} placeholder="Enter your password" />
                    <button type="button" className="absolute top-1/2 right-3 flex size-8 -translate-y-1/2 items-center justify-center rounded-lg text-white/30 transition hover:bg-white/6 hover:text-white" onClick={() => setShowPassword(value => !value)} aria-label={showPassword ? "Hide password" : "Show password"}>
                      {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                    </button>
                  </span>
                </label>

                {startupMessage ? <p role="status" className="rounded-xl border border-cyan-300/16 bg-cyan-300/8 px-4 py-3 text-sm text-cyan-100">{startupMessage}</p> : null}
                {error ? <p role="alert" className="rounded-xl border border-rose-400/16 bg-rose-400/8 px-4 py-3 text-sm text-rose-200">{error}</p> : null}

                <button type="submit" disabled={busy} className="auth-submit group relative flex h-13 w-full items-center justify-center overflow-hidden rounded-xl font-semibold text-white disabled:cursor-wait">
                  <span className="auth-submit-shine" aria-hidden="true" />
                  {busy ? <><LoaderCircle className="mr-2 size-4 animate-spin" /> {startupMessage ? "Starting workspace…" : "Opening your path…"}</> : <>{login ? "Enter your workspace" : "Begin your journey"}<ArrowRight className="ml-2 size-4 transition-transform group-hover:translate-x-1" /></>}
                </button>
              </form>

              <div className="mt-6 flex items-start justify-center gap-2 text-center text-[11px] leading-5 text-white/34 sm:items-center sm:text-xs">
                <LockKeyhole className="mt-0.5 size-3.5 shrink-0 text-emerald-300/70 sm:mt-0" />
                Private account · Isolated data · Your progress
              </div>

              <button type="button" className="mx-auto mt-6 flex items-center gap-1 text-sm text-white/48 transition hover:text-white" onClick={() => changeMode(login ? "signup" : "login")}>
                {login ? "New to Data Lab? Create your space" : "Already building? Sign in"}
                <ChevronRight className="size-3.5" />
              </button>
            </div>
          </section>
        </div>

        {unlocking ? (
          <div className="auth-unlock-stage absolute inset-0 z-40 grid place-items-center overflow-hidden bg-[#060711]" role="status" aria-live="polite">
            <div className="auth-unlock-light" aria-hidden="true" />
            <div className="auth-door auth-door-left" aria-hidden="true"><span /></div>
            <div className="auth-door auth-door-right" aria-hidden="true"><span /></div>
            <div className="auth-unlock-message relative z-20 text-center">
              <span className="mx-auto flex size-16 items-center justify-center rounded-2xl border border-emerald-300/25 bg-emerald-300/10 text-emerald-200 shadow-[0_0_60px_rgba(110,231,183,.25)]"><Check className="size-7" /></span>
              <p className="mt-6 text-xs tracking-[.28em] text-emerald-200/75 uppercase">Path unlocked</p>
              <h2 className="mt-3 text-3xl font-semibold tracking-tight">Your next chapter is opening.</h2>
            </div>
          </div>
        ) : null}
      </DialogContent>
    </Dialog>
  );
}
