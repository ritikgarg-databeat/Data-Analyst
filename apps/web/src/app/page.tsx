import {
  ArrowRight,
  BarChart3,
  Binary,
  Bot,
  BriefcaseBusiness,
  ChartNoAxesCombined,
  Check,
  Code2,
  Database,
  GraduationCap,
  LineChart,
  Network,
  Play,
  ShieldCheck,
  Sparkles,
  Target,
  TerminalSquare,
  TrendingUp,
  Zap,
} from "lucide-react";
import Link from "next/link";
import type { CSSProperties } from "react";

import { LandingAuthExperience, LandingAuthTrigger } from "@/components/features/landing/landing-auth-experience";

const features = [
  {
    icon: GraduationCap,
    title: "A curriculum that moves with you",
    description: "Build durable skills through focused lessons, practice loops, and progress-aware recommendations.",
    color: "from-violet-500/20 to-fuchsia-500/5 text-violet-300",
  },
  {
    icon: TerminalSquare,
    title: "Practice in real labs",
    description: "Write SQL, explore Python, profile datasets, model data, and turn concepts into working analysis.",
    color: "from-cyan-500/20 to-blue-500/5 text-cyan-300",
  },
  {
    icon: Bot,
    title: "AI help with context",
    description: "Get guidance grounded in your learning path, work, and goals—when your administrator enables it.",
    color: "from-pink-500/20 to-rose-500/5 text-pink-300",
  },
  {
    icon: Target,
    title: "Career-ready outcomes",
    description: "Connect practice to projects, interview preparation, portfolio evidence, and measurable growth.",
    color: "from-amber-500/20 to-orange-500/5 text-amber-300",
  },
];

const tracks = ["SQL", "Python", "Statistics", "Visualization", "Data Modeling", "Product Analytics"];

const curriculumStages = [
  {
    number: "01",
    label: "Build the foundation",
    title: "Data thinking, Excel & SQL",
    description: "Learn to frame questions, clean messy inputs, and query data with confidence.",
    skills: ["Data literacy", "Spreadsheets", "SQL"],
    icon: Database,
    tone: "violet",
  },
  {
    number: "02",
    label: "Find the signal",
    title: "Python & statistics",
    description: "Explore, test, and automate analysis using the tools working analysts rely on.",
    skills: ["Python", "Pandas", "Statistics"],
    icon: Code2,
    tone: "cyan",
  },
  {
    number: "03",
    label: "Explain the insight",
    title: "Visualization & storytelling",
    description: "Turn analysis into clear charts, dashboards, and decisions people can act on.",
    skills: ["Dashboards", "Storytelling", "BI"],
    icon: LineChart,
    tone: "fuchsia",
  },
  {
    number: "04",
    label: "Work like a modern team",
    title: "Modeling & the data stack",
    description: "Build reliable datasets and understand how analytics work moves into production.",
    skills: ["Data modeling", "dbt", "Warehousing"],
    icon: Network,
    tone: "amber",
  },
  {
    number: "05",
    label: "Prove what you can do",
    title: "Projects & career readiness",
    description: "Create portfolio evidence, practice interviews, and connect every skill to a role.",
    skills: ["Case studies", "Portfolio", "Interviews"],
    icon: BriefcaseBusiness,
    tone: "emerald",
  },
] as const;

const journey = [
  ["01", "Learn", "Follow a modern path that turns complex topics into clear, achievable steps."],
  ["02", "Practice", "Use realistic exercises, datasets, labs, and cases—not passive video-only learning."],
  ["03", "Build", "Create projects and a body of work that proves what you can do."],
];

const dashboardMetrics = [
  ["Progress", "68%", BarChart3],
  ["Skills", "7 / 12", Zap],
  ["Projects", "4", Code2],
  ["Readiness", "82", LineChart],
] as const;

const dataSignals = ["SELECT *", "{ insight }", "+42%", "PYTHON", "σ = 0.84", "JOIN", "01", "AI READY"];

const careerProof = [
  [GraduationCap, "Learn", "A guided path, not a content maze"],
  [TerminalSquare, "Practice", "Real labs, datasets, and decisions"],
  [BriefcaseBusiness, "Prove", "Projects that show how you think"],
] as const;

export default function LandingPage() {
  return (
    <LandingAuthExperience>
    <main className="landing-page min-h-svh overflow-x-clip bg-[#070914] text-white">
      <header className="fixed inset-x-0 top-0 z-50 border-b border-white/8 bg-[#070914]/75 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-7xl items-center px-5 sm:px-8">
          <Link href="/" className="flex items-center gap-2.5 font-semibold tracking-tight" aria-label="Data Lab home">
            <span className="landing-logo flex size-9 items-center justify-center rounded-xl">
              <Sparkles className="size-4.5" aria-hidden="true" />
            </span>
            <span className="text-lg">Data Lab</span>
          </Link>
          <nav className="ml-12 hidden items-center gap-8 text-sm text-white/60 md:flex lg:hidden xl:flex" aria-label="Landing page">
            <a className="transition-colors hover:text-white" href="#curriculum">Curriculum</a>
            <a className="transition-colors hover:text-white" href="#features">Workspace</a>
            <a className="transition-colors hover:text-white" href="#ai">AI guidance</a>
          </nav>
          <div className="pointer-events-none absolute left-1/2 hidden -translate-x-1/2 items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3.5 py-1.5 text-xs font-medium tracking-wide text-white/55 lg:flex">
            <Code2 className="size-3.5 text-cyan-300" aria-hidden="true" />
            <span>Built and Engineered by Ritik Garg</span>
          </div>
          <div className="ml-auto flex items-center gap-2.5">
            <LandingAuthTrigger mode="login" className="rounded-full px-4 py-2 text-sm font-medium text-white/75 transition hover:bg-white/8 hover:text-white">Sign in</LandingAuthTrigger>
            <LandingAuthTrigger mode="signup" className="landing-button hidden items-center rounded-full px-5 py-2.5 text-sm font-semibold sm:inline-flex">Start learning <ArrowRight className="ml-2 size-4" aria-hidden="true" /></LandingAuthTrigger>
          </div>
        </div>
      </header>

      <section className="relative isolate px-5 pb-24 pt-32 sm:px-8 sm:pt-40 lg:pb-32">
        <div className="landing-orb landing-orb-one" aria-hidden="true" />
        <div className="landing-orb landing-orb-two" aria-hidden="true" />
        <div className="landing-grid absolute inset-0 -z-10 opacity-45" aria-hidden="true" />
        <div className="landing-data-field absolute inset-0 -z-10 overflow-hidden" aria-hidden="true">
          {dataSignals.map((signal, index) => (
            <span key={signal} className="landing-data-signal" style={{ "--signal-index": index } as CSSProperties}>{signal}</span>
          ))}
          <svg viewBox="0 0 1200 620" className="landing-signal-lines absolute inset-x-0 top-10 h-155 w-full opacity-45">
            <path d="M-40 470 C160 510 206 225 390 318 S661 375 750 188 S1040 61 1250 135" />
            <path d="M-40 555 C180 406 270 565 482 428 S781 280 1250 356" />
          </svg>
        </div>
        <div className="mx-auto max-w-7xl">
          <div className="mx-auto max-w-4xl text-center">
            <div className="landing-reveal mx-auto inline-flex items-center gap-2 rounded-full border border-violet-300/20 bg-violet-400/8 px-3.5 py-1.5 text-xs font-medium text-violet-200">
              <span className="relative flex size-2"><span className="absolute inline-flex size-full animate-ping rounded-full bg-fuchsia-400 opacity-60" /><span className="relative inline-flex size-2 rounded-full bg-fuchsia-400" /></span>
              AI-powered learning. Real career momentum.
            </div>
            <h1 className="landing-reveal landing-delay-1 mt-7 text-[clamp(2.65rem,12vw,4.5rem)] leading-[0.98] font-semibold tracking-[-0.055em] text-balance lg:text-[5.75rem]">
              Learn real data skills. <span className="landing-gradient-text block">Build proof. Walk in ready.</span>
            </h1>
            <p className="landing-reveal landing-delay-2 mx-auto mt-7 max-w-2xl text-lg leading-8 text-white/60 sm:text-xl">
              Your personal data lab combines a modern curriculum, hands-on practice, portfolio projects, and career preparation in one focused workspace.
            </p>
            <div className="landing-reveal landing-delay-3 mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row">
              <LandingAuthTrigger mode="signup" className="landing-button group inline-flex h-13 items-center justify-center rounded-full px-7 text-sm font-semibold">Create your free account <ArrowRight className="ml-2 size-4 transition-transform group-hover:translate-x-1" aria-hidden="true" /></LandingAuthTrigger>
              <a href="#curriculum" className="inline-flex h-13 items-center justify-center rounded-full border border-white/12 bg-white/5 px-7 text-sm font-semibold text-white/80 transition hover:border-white/25 hover:bg-white/9 hover:text-white"><Play className="mr-2 size-4 fill-current" aria-hidden="true" /> Explore the curriculum</a>
            </div>
            <div className="landing-reveal landing-delay-4 mt-7 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs text-white/45">
              <span className="flex items-center gap-1.5"><Check className="size-3.5 text-emerald-400" /> Separate private workspace</span>
              <span className="flex items-center gap-1.5"><Check className="size-3.5 text-emerald-400" /> Progress that stays with you</span>
              <span className="flex items-center gap-1.5"><Check className="size-3.5 text-emerald-400" /> Built for active practice</span>
            </div>
          </div>

          <div className="landing-reveal landing-delay-4 landing-hero-stage relative mx-auto mt-16 max-w-5xl">
            <div className="absolute -inset-8 -z-10 bg-violet-500/10 blur-3xl" />
            <div className="landing-float-card landing-float-card-left absolute top-23 -left-28 z-20 hidden items-center gap-3 rounded-xl border border-white/10 bg-[#0d1020]/85 px-4 py-3 shadow-2xl backdrop-blur-xl xl:flex">
              <span className="flex size-8 items-center justify-center rounded-lg bg-emerald-400/10 text-emerald-300"><TrendingUp className="size-4" /></span>
              <span><strong className="block text-xs">Readiness rising</strong><small className="text-[10px] text-white/35">+18% this month</small></span>
            </div>
            <div className="landing-float-card landing-float-card-right absolute right-[-7.5rem] bottom-20 z-20 hidden items-center gap-3 rounded-xl border border-white/10 bg-[#0d1020]/85 px-4 py-3 shadow-2xl backdrop-blur-xl xl:flex">
              <span className="flex size-8 items-center justify-center rounded-lg bg-cyan-400/10 text-cyan-300"><Binary className="size-4" /></span>
              <span><strong className="block text-xs">SQL mastered</strong><small className="text-[10px] text-white/35">Portfolio proof added</small></span>
            </div>
            <div className="landing-window overflow-hidden rounded-2xl border border-white/12 bg-[#0d1020]/92 shadow-2xl shadow-violet-950/50">
              <div className="flex h-11 items-center border-b border-white/8 px-4">
                <div className="flex gap-1.5"><span className="size-2.5 rounded-full bg-rose-400/70" /><span className="size-2.5 rounded-full bg-amber-400/70" /><span className="size-2.5 rounded-full bg-emerald-400/70" /></div>
                <div className="mx-auto rounded-md border border-white/7 bg-white/4 px-12 py-1 text-[10px] text-white/30">Data Lab workspace</div>
              </div>
              <div className="grid min-h-105 sm:grid-cols-[160px_1fr]">
                <aside className="hidden border-r border-white/7 p-4 sm:block">
                  <div className="mb-6 flex items-center gap-2 text-xs font-semibold"><span className="landing-logo flex size-6 items-center justify-center rounded-md"><Sparkles className="size-3" /></span> Data Lab</div>
                  {["Overview", "Learn", "Practice", "Datasets", "Projects"].map((item, index) => <div key={item} className={`mb-1 rounded-md px-2.5 py-2 text-[11px] ${index === 0 ? "bg-violet-400/12 text-violet-200" : "text-white/35"}`}>{item}</div>)}
                </aside>
                <div className="p-5 sm:p-7">
                  <div className="flex flex-col items-start gap-3 min-[430px]:flex-row min-[430px]:justify-between"><div className="min-w-0"><p className="text-xs text-violet-300">Welcome back</p><h2 className="mt-1 text-lg font-semibold sm:text-xl">Your Personal Data Lab</h2></div><span className="shrink-0 rounded-full bg-emerald-400/10 px-2.5 py-1 text-[10px] text-emerald-300">5 day streak</span></div>
                  <div className="mt-6 grid grid-cols-2 gap-3 lg:grid-cols-4">
                    {dashboardMetrics.map(([label, value, Icon]) => <div key={label} className="rounded-xl border border-white/7 bg-white/[0.035] p-3.5"><Icon className="size-3.5 text-violet-300" /><p className="mt-4 text-lg font-semibold">{value}</p><p className="text-[10px] text-white/35">{label}</p></div>)}
                  </div>
                  <div className="mt-4 grid gap-4 lg:grid-cols-[1.35fr_1fr]">
                    <div className="rounded-xl border border-white/7 bg-white/[0.035] p-4"><div className="flex items-center justify-between text-xs"><span className="font-medium">Learning momentum</span><span className="text-emerald-300">+18%</span></div><div className="mt-7 flex h-24 items-end gap-2">{[38, 54, 45, 66, 58, 83, 74, 94].map((height, index) => <span key={index} className="landing-bar flex-1 rounded-t-sm" style={{ height: `${height}%`, animationDelay: `${index * 90}ms` }} />)}</div></div>
                    <div className="rounded-xl border border-white/7 bg-white/[0.035] p-4"><p className="text-xs font-medium">Next up</p><div className="mt-4 rounded-lg bg-violet-400/9 p-3"><Database className="size-4 text-violet-300" /><p className="mt-3 text-xs font-medium">SQL window functions</p><p className="mt-1 text-[10px] text-white/35">18 min · Intermediate</p><div className="mt-3 h-1 overflow-hidden rounded-full bg-white/8"><div className="h-full w-2/3 rounded-full bg-gradient-to-r from-violet-400 to-fuchsia-400" /></div></div></div>
                  </div>
                </div>
              </div>
            </div>
            <div className="landing-proof-rail relative z-20 mx-auto -mt-px grid max-w-4xl gap-px overflow-hidden rounded-b-2xl border border-white/10 bg-white/8 sm:grid-cols-3">
              {careerProof.map(([Icon, title, description], index) => (
                <div key={title} className="landing-proof-rail-item group flex items-center gap-3 bg-[#0b0e1b]/95 px-5 py-4">
                  <span className="flex size-9 shrink-0 items-center justify-center rounded-xl border border-violet-300/12 bg-violet-400/8 text-violet-200"><Icon className="size-4" /></span>
                  <span><strong className="block text-xs font-semibold text-white/85">{title}</strong><small className="mt-0.5 block text-[10px] leading-4 text-white/38">{description}</small></span>
                  {index < careerProof.length - 1 && <ArrowRight className="ml-auto hidden size-3.5 text-violet-300/40 sm:block" aria-hidden="true" />}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="landing-ticker-shell border-y border-white/7 bg-white/[0.018] py-5" aria-label="Learning tracks">
        <div className="landing-ticker flex w-max items-center gap-10 text-sm font-medium text-white/36">
          {[...tracks, ...tracks, ...tracks].map((track, index) => <span key={`${track}-${index}`} className="flex items-center gap-10"><span>{track}</span><span className="size-1 rounded-full bg-violet-400/60" /></span>)}
        </div>
      </section>

      <section id="curriculum" className="landing-curriculum-section relative isolate overflow-x-clip border-y border-white/7 px-3 py-20 min-[380px]:px-5 sm:px-8 sm:py-24 lg:py-32">
        <div className="landing-grid absolute inset-0 -z-20 opacity-20" aria-hidden="true" />
        <div className="landing-curriculum-glow absolute top-24 left-1/2 -z-10 h-96 w-3/4 -translate-x-1/2 rounded-full bg-violet-600/12 blur-[110px]" aria-hidden="true" />
        <div className="mx-auto max-w-7xl">
          <div className="mx-auto max-w-4xl text-center">
            <div className="inline-flex items-center gap-2 rounded-full border border-cyan-300/18 bg-cyan-300/7 px-3.5 py-1.5 text-xs font-medium text-cyan-200"><Sparkles className="size-3.5" /> The heart of Data Lab</div>
            <h2 className="mt-6 text-3xl leading-[1.02] font-semibold tracking-[-0.045em] text-balance min-[380px]:text-4xl sm:text-6xl">A complete path from <span className="landing-gradient-text">first query to career-ready.</span></h2>
            <p className="mx-auto mt-6 max-w-2xl text-base leading-7 text-white/52 sm:text-lg sm:leading-8">No guessing what to learn next. Every lesson leads into practice, every practice builds judgment, and every project becomes proof.</p>
            <div className="mt-8 flex flex-wrap justify-center gap-2.5">
              {["Guided lessons", "Hands-on labs", "Real datasets", "Portfolio projects", "Interview practice"].map(item => <span key={item} className="rounded-full border border-white/9 bg-white/4 px-3.5 py-2 text-xs text-white/58"><Check className="mr-1.5 inline size-3 text-emerald-300" />{item}</span>)}
            </div>
          </div>

          <div className="landing-curriculum-shell relative mt-12 min-w-0 overflow-hidden rounded-[2rem] border border-white/10 bg-[#0a0d1a]/94 shadow-2xl shadow-violet-950/35 sm:mt-16">
            <div className="landing-curriculum-beam absolute inset-x-0 top-0 h-px" aria-hidden="true" />
            <div className="border-b border-white/8 px-5 py-5 sm:px-8">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div><p className="text-xs font-medium tracking-[0.2em] text-violet-300 uppercase">Your learning path</p><p className="mt-1 text-sm text-white/42">Five connected stages. One clear outcome.</p></div>
                <div className="flex items-center gap-2 text-xs text-white/38"><span className="relative flex size-2"><span className="absolute inline-flex size-full animate-ping rounded-full bg-emerald-400 opacity-50" /><span className="relative size-2 rounded-full bg-emerald-400" /></span> Progress adapts as you grow</div>
              </div>
            </div>

            <div className="grid min-w-0 lg:grid-cols-[minmax(0,1.08fr)_minmax(0,.92fr)]">
              <div className="landing-curriculum-route min-w-0 p-2.5 min-[380px]:p-4 sm:p-7 lg:border-r lg:border-white/8">
                {curriculumStages.map(({ number, label, title, description, skills, icon: Icon, tone }, index) => (
                  <article key={number} data-tone={tone} className="landing-curriculum-card group relative mb-3 grid min-w-0 grid-cols-[2.75rem_minmax(0,1fr)] gap-3 rounded-2xl border border-white/7 bg-white/[0.025] p-3 last:mb-0 min-[380px]:grid-cols-[3rem_minmax(0,1fr)] min-[380px]:gap-4 min-[380px]:p-4 sm:p-5">
                    <div className="relative flex min-w-0 flex-col items-center">
                      <span className="landing-curriculum-node relative z-10 flex size-11 items-center justify-center rounded-2xl border bg-[#111526] shadow-lg min-[380px]:size-12"><Icon className="size-5" /></span>
                      <span className="mt-2 block font-mono text-[10px] tracking-[0.18em] text-white/28">{number}</span>
                    </div>
                    <div className="min-w-0">
                      <div className="flex min-w-0 flex-col items-start gap-2 min-[430px]:flex-row min-[430px]:items-center min-[430px]:justify-between"><p className="min-w-0 text-[9px] font-semibold tracking-[0.14em] text-white/36 uppercase min-[380px]:text-[10px] min-[380px]:tracking-[0.17em]">{label}</p>{index === 0 && <span className="shrink-0 rounded-full border border-emerald-300/15 bg-emerald-300/7 px-2 py-1 text-[9px] font-medium text-emerald-200">Start here</span>}</div>
                      <h3 className="mt-1.5 text-base font-semibold text-white/88 min-[380px]:text-lg">{title}</h3>
                      <p className="mt-2 max-w-xl text-sm leading-6 text-white/42">{description}</p>
                      <div className="mt-3 flex flex-wrap gap-1.5">{skills.map(skill => <span key={skill} className="landing-skill-chip rounded-md border border-white/7 bg-black/15 px-2 py-1 text-[10px] text-white/46">{skill}</span>)}</div>
                    </div>
                  </article>
                ))}
              </div>

              <aside className="landing-curriculum-preview relative flex min-w-0 flex-col border-t border-white/8 p-4 min-[380px]:p-5 sm:p-8 lg:border-t-0" aria-label="Curriculum practice preview">
                <div className="flex min-w-0 items-center justify-between gap-3"><div className="min-w-0"><p className="text-xs font-medium text-cyan-300">Practice, not passive watching</p><h3 className="mt-2 text-xl font-semibold sm:text-2xl">See a skill become evidence.</h3></div><span className="hidden size-11 shrink-0 items-center justify-center rounded-2xl border border-cyan-300/14 bg-cyan-300/7 text-cyan-200 sm:flex"><ChartNoAxesCombined className="size-5" /></span></div>
                <p className="mt-3 text-sm leading-6 text-white/42">A concept moves straight into a realistic lab, feedback, and something worth showing.</p>

                <div className="mt-7 min-w-0 overflow-hidden rounded-2xl border border-white/9 bg-[#070914] shadow-xl">
                  <div className="flex h-10 min-w-0 items-center border-b border-white/7 px-3 sm:px-4"><span className="size-2 shrink-0 rounded-full bg-rose-400/70" /><span className="ml-1.5 size-2 shrink-0 rounded-full bg-amber-400/70" /><span className="ml-1.5 size-2 shrink-0 rounded-full bg-emerald-400/70" /><span className="ml-auto min-w-0 truncate pl-3 font-mono text-[9px] text-white/25">retention_analysis.sql</span></div>
                  <pre className="max-w-full overflow-x-auto p-3 font-mono text-[10px] leading-5 whitespace-pre-wrap text-white/56 min-[380px]:p-4 sm:p-5 sm:text-[11px] sm:leading-6 sm:whitespace-pre"><code><span className="text-fuchsia-300">WITH</span> cohorts <span className="text-fuchsia-300">AS</span> ({"\n"}  <span className="text-violet-300">SELECT</span> customer_id,{"\n"}    <span className="text-cyan-300">DATE_TRUNC</span>(&apos;month&apos;, joined_at) cohort{"\n"}  <span className="text-violet-300">FROM</span> customers{"\n"}){"\n"}<span className="text-violet-300">SELECT</span> cohort, <span className="text-cyan-300">COUNT</span>(*) retained_users</code></pre>
                  <div className="grid grid-cols-3 border-t border-white/7 bg-white/[0.025]">
                    {[['Rows', '12.4k'], ['Insight', '+18%'], ['Checks', 'Passed']].map(([label, value]) => <div key={label} className="border-r border-white/7 px-3 py-3 text-center last:border-0"><strong className="block text-xs text-white/78">{value}</strong><span className="mt-0.5 block text-[9px] text-white/28">{label}</span></div>)}
                  </div>
                </div>

                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <div className="landing-outcome-card rounded-2xl border border-violet-300/12 bg-violet-400/6 p-4"><Code2 className="size-4 text-violet-300" /><p className="mt-4 text-sm font-semibold">Portfolio evidence</p><p className="mt-1 text-[11px] leading-5 text-white/36">Document the question, method, and business recommendation.</p></div>
                  <div className="landing-outcome-card rounded-2xl border border-cyan-300/12 bg-cyan-400/6 p-4"><TrendingUp className="size-4 text-cyan-300" /><p className="mt-4 text-sm font-semibold">Visible progress</p><p className="mt-1 text-[11px] leading-5 text-white/36">See capability grow across skills, projects, and readiness.</p></div>
                </div>

                <div className="mt-auto pt-7">
                  <LandingAuthTrigger mode="signup" className="landing-button group inline-flex h-12 w-full items-center justify-center rounded-xl px-6 text-sm font-semibold">Start the curriculum <ArrowRight className="ml-2 size-4 transition-transform group-hover:translate-x-1" /></LandingAuthTrigger>
                  <p className="mt-3 text-center text-[10px] text-white/28">Begin with foundations. Grow at your own pace.</p>
                </div>
              </aside>
            </div>
          </div>
        </div>
      </section>

      <section id="features" className="px-5 py-24 sm:px-8 lg:py-32">
        <div className="mx-auto max-w-7xl">
          <div className="max-w-2xl"><p className="text-sm font-medium text-violet-300">Everything connects</p><h2 className="mt-3 text-3xl font-semibold tracking-tight text-balance sm:text-5xl">One lab for the whole learning journey.</h2><p className="mt-5 text-lg leading-8 text-white/50">No scattered tools or disconnected progress. Learn concepts, apply them, and see your growth in one private workspace.</p></div>
          <div className="mt-14 grid gap-4 md:grid-cols-2">{features.map(({ icon: Icon, title, description, color }) => <article key={title} className="landing-feature group relative overflow-hidden rounded-2xl border border-white/8 bg-white/[0.025] p-7 sm:p-8"><div className={`inline-flex size-11 items-center justify-center rounded-xl bg-gradient-to-br ${color}`}><Icon className="size-5" /></div><h3 className="mt-8 text-xl font-semibold">{title}</h3><p className="mt-3 max-w-md leading-7 text-white/48">{description}</p><div className="absolute -right-20 -bottom-20 size-48 rounded-full bg-violet-500/8 blur-3xl transition group-hover:bg-violet-500/15" /></article>)}</div>
        </div>
      </section>

      <section id="journey" className="px-5 py-24 sm:px-8 lg:py-32">
        <div className="mx-auto max-w-7xl"><div className="text-center"><p className="text-sm font-medium text-fuchsia-300">A simple rhythm</p><h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-5xl">Learn. Practice. Build.</h2></div><div className="relative mt-16 grid gap-10 md:grid-cols-3"><div className="absolute top-8 right-[16%] left-[16%] hidden h-px bg-gradient-to-r from-transparent via-violet-400/35 to-transparent md:block" />{journey.map(([number, title, description]) => <article key={number} className="relative text-center"><span className="mx-auto flex size-16 items-center justify-center rounded-2xl border border-violet-300/18 bg-violet-400/8 text-sm font-semibold text-violet-200 shadow-xl shadow-violet-950/20">{number}</span><h3 className="mt-6 text-xl font-semibold">{title}</h3><p className="mx-auto mt-3 max-w-sm leading-7 text-white/45">{description}</p></article>)}</div></div>
      </section>

      <section id="ai" className="px-5 pb-24 pt-24 sm:px-8 lg:py-32">
        <div className="relative mx-auto max-w-7xl overflow-hidden rounded-3xl border border-violet-300/14 bg-gradient-to-br from-violet-500/13 via-fuchsia-500/7 to-cyan-500/8 px-6 py-16 text-center sm:px-12 sm:py-20"><div className="landing-grid absolute inset-0 opacity-25" /><div className="relative"><span className="mx-auto flex size-12 items-center justify-center rounded-2xl border border-white/12 bg-white/8"><Bot className="size-5 text-violet-200" /></span><p className="mt-6 text-sm font-medium text-violet-200">AI that supports the work</p><h2 className="mx-auto mt-3 max-w-3xl text-3xl font-semibold tracking-tight text-balance sm:text-5xl">Guidance when you need it. Ownership stays with you.</h2><p className="mx-auto mt-5 max-w-2xl text-lg leading-8 text-white/52">Use contextual AI assistance to unblock learning and sharpen thinking while your progress, datasets, and workspace remain private to your account.</p><div className="mt-7 flex flex-wrap justify-center gap-5 text-xs text-white/45"><span className="flex items-center gap-2"><ShieldCheck className="size-4 text-emerald-300" /> Per-user access controls</span><span className="flex items-center gap-2"><Zap className="size-4 text-amber-300" /> Usage-aware quotas</span><span className="flex items-center gap-2"><Database className="size-4 text-cyan-300" /> Isolated user data</span></div></div></div>
      </section>

      <section className="border-t border-white/7 px-5 py-24 sm:px-8"><div className="mx-auto max-w-3xl text-center"><h2 className="text-3xl font-semibold tracking-tight text-balance sm:text-5xl">Your next skill starts here.</h2><p className="mx-auto mt-5 max-w-xl text-lg text-white/50">Create your private workspace and turn steady practice into work you are proud to show.</p><LandingAuthTrigger mode="signup" className="landing-button group mt-8 inline-flex h-13 items-center justify-center rounded-full px-7 text-sm font-semibold">Start with Data Lab <ArrowRight className="ml-2 size-4 transition-transform group-hover:translate-x-1" /></LandingAuthTrigger></div></section>

      <footer className="border-t border-white/7 px-5 py-8 sm:px-8"><div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 text-xs text-white/32 sm:flex-row"><Link href="/" className="flex items-center gap-2 text-sm font-semibold text-white/70"><span className="landing-logo flex size-7 items-center justify-center rounded-lg"><Sparkles className="size-3" /></span>Data Lab</Link><p>Learn with focus. Build with confidence.</p><div className="flex gap-5"><LandingAuthTrigger mode="login" className="hover:text-white">Sign in</LandingAuthTrigger><LandingAuthTrigger mode="signup" className="hover:text-white">Create account</LandingAuthTrigger><Link className="hover:text-white" href="/admin/login">Admin</Link></div></div></footer>
    </main>
    </LandingAuthExperience>
  );
}
