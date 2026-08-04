# CausalLens — Master Build Spec

**Read this entire file before writing any code.** This is the single source of truth: problem, requirements, architecture, UI/UX rules, dos and don'ts, and the phased build plan. Build in the order given in "Build Plan," self-verify each phase before moving to the next, git micro-commit after each working phase, and never stop to ask "should I continue" — keep going until a phase is genuinely blocked.

---

## 1. Why This Project Exists

Ved (business analytics postgrad, fresher BA candidate) already has three portfolio projects: a smart-grid dashboard (ADFlex), a product retention analytics dashboard (RetentionIQ), and an AI text-to-SQL insight agent (InsightPilot). All three are strong, but none of them prove the one skill that separates a real analyst from someone who can build a dashboard: **knowing whether an observed difference is real, or noise.**

Almost every fresher BA portfolio stops at descriptive statistics — a chart, a KPI, a trend line. CausalLens goes one level deeper: given two groups (or a before/after change), it tells you rigorously whether the difference is statistically real, how confident you should be, and whether you have enough data to trust the answer. That is the actual, everyday judgment call a business analyst is hired to make — "did the campaign work, or did we get lucky" — and almost nobody at fresher level can demonstrate it with real statistics instead of a gut call.

This project exists to prove: hypothesis testing done correctly (not a naive t-test), Bayesian inference as a second lens, causal inference when there's no clean A/B test to lean on, and — critically — the ability to translate all of that into a plain-English business verdict a non-technical stakeholder would trust.

---

## 2. The Problem It Solves

A business team runs an experiment (new checkout flow, new price, new ad creative) or makes a change without a controlled test (a marketing campaign launch, a policy change). They see a metric move. Two questions follow, and most teams answer both badly:

1. Is this movement real, or could it just be random noise? (Most people eyeball two numbers and declare a winner — this is how false positives and "significant" results that don't replicate happen.)
2. If there was no control group, how do we know the change *caused* the movement, rather than a coincidence of timing, seasonality, or an external trend?

CausalLens answers both, with the actual statistical methods used in industry (Optimizely/Statsig-style experimentation platforms, and Google's CausalImpact-style analysis), wrapped in an interface a business stakeholder can read without a stats background.

---

## 3. Who It's For

Primary persona: a data/growth/product team lead who ran a test or shipped a change and needs a trustworthy answer, fast, without opening a stats textbook. Secondary persona (who actually matters for the portfolio): the hiring manager reading Ved's CV, who sees "built a rigorous A/B testing and causal inference platform" and immediately understands this candidate thinks like an analyst, not a dashboard builder.

---

## 4. Core Features (MVP Scope — build exactly this, nothing more)

### 4.1 Data input
Two ways to get data in, both required:
- **Synthetic data generator** (build this first — it is the backbone of the whole project). User sets: baseline conversion rate or mean, true effect size (including "zero" to test for false positives), sample size per group, and noise/variance. The app generates control and treatment data with that *known ground truth*. This lets every statistical method in the app be validated live, in front of the user — "the true effect was 2%, here's what each method concluded." This is the single most convincing thing in the whole project for a hiring manager, because it proves the methods actually work rather than just running library calls.
- **CSV upload**: two-column (group, outcome) or four-column (date, group, metric_numerator, metric_denominator) for real or Kaggle-sourced A/B test datasets.

### 4.2 Classical hypothesis testing module
- Two-proportion z-test (conversion-rate style metrics)
- Two-sample t-test (Welch's, not pooled — don't assume equal variance) for continuous metrics
- Mann-Whitney U as the non-parametric fallback when the data is visibly non-normal (detect this automatically via a normality check, e.g. Shapiro-Wilk on a sample, and recommend the right test — don't make the user choose blind)
- Report: p-value, confidence interval on the difference, effect size (Cohen's d or relative lift %), and a plain-English verdict

### 4.3 Power analysis
- Given a minimum detectable effect (MDE) and baseline rate/variance, compute required sample size per group before running the test
- Given the actual sample size collected, compute achieved statistical power — so the user can see "you didn't have enough data to detect an effect this small" instead of wrongly concluding "no effect"

### 4.4 Sequential testing / peeking correction
- Implement at least one peeking-safe method (mSPRT or an alpha-spending approach) and show, side-by-side with the naive fixed-horizon test, how "peeking" at results daily inflates false positive rate if you don't correct for it. This is the detail that signals real statistical maturity — most people don't know this is a problem at all.

### 4.5 Bayesian A/B testing module
- Beta-Binomial conjugate model for conversion-rate metrics: posterior distributions for control and treatment, P(treatment > control), expected loss if you ship the wrong variant, and a 95% credible interval on the lift
- This is analytically tractable (no MCMC needed, keeps it fast and free-tier friendly) — use closed-form Beta-Binomial math, not a sampling library, unless conjugacy doesn't apply to the metric type

### 4.6 Causal impact module (for changes with no control group)
- Difference-in-differences: user provides a treated unit's before/after series and a comparable untreated control series (e.g., treated region vs. untreated region), computes the DiD estimate and its significance
- A lightweight counterfactual/structural time-series method (e.g., statsmodels UnobservedComponents local-level model, or a simple synthetic-control-style weighted combination of control series) to estimate "what would have happened without the change" and quantify the gap as the causal effect, with a confidence band
- Must explicitly flag the assumptions the method relies on (parallel trends for DiD, no other confounding shocks) — a real analyst names their assumptions instead of hiding them

### 4.7 Multiple testing correction
- When a user tests several metrics/segments at once, apply Benjamini-Hochberg (FDR control) and show how many "significant" results would have been false positives without it

### 4.8 The verdict layer (this is the product, not a bonus feature)
Every module ends in a single, auto-generated plain-English summary block: what was tested, what the data shows, how confident you should be, whether there's enough data to trust the answer, and a recommendation (ship / don't ship / needs more data / can't determine causally). This is what turns "a stats app" into "a business analytics product" — never let raw statistical output be the only thing the user sees.

### Explicitly out of scope for MVP
Multi-armed bandits, full MCMC/PyMC Bayesian models, real-time streaming data, user accounts/auth, multi-tenant saved projects. Two people won't remember this app for its user management. They'll remember it for whether it explains statistics correctly.

---

## 5. Tech Stack

Match the stack already proven across the other portfolio projects — stay on free tiers throughout:

- **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind CSS, Recharts for distribution/CI/credible-interval visualizations
- **Backend:** FastAPI (Python) — this is where the statistical engine lives: `scipy.stats`, `statsmodels`, plain NumPy for the Beta-Binomial Bayesian math. No heavy ML/MCMC dependencies.
- **Database:** Neon Postgres (free tier) — stores uploaded datasets and past analysis runs so results are shareable via a link, not just session state
- **Hosting:** Frontend on Vercel, backend on Render, both free tier
- **Repo:** new GitHub repo, e.g. `git@github.com:vedjr02/CausalLens.git`, branch `main`

---

## 6. Architecture Overview

```
User uploads CSV or configures synthetic generator (Next.js)
        │
        ▼
FastAPI /analyze endpoint receives data + selected test type
        │
        ▼
Statistical engine (Python):
  - normality check → recommend test
  - run classical test (z/t/Mann-Whitney)
  - run power analysis
  - run sequential-testing comparison
  - run Bayesian Beta-Binomial (if applicable)
  - run causal module (if DiD/time-series mode selected)
  - apply multiple-testing correction (if multi-metric)
        │
        ▼
Verdict generator: turns numeric output into a plain-English
recommendation block
        │
        ▼
Results persisted to Neon Postgres (shareable run ID)
        │
        ▼
Next.js renders: distribution charts, CI/credible interval bars,
verdict card, "how confident should you be" explainer
```

---

## 7. UI/UX Rules

- Apple-level minimalist. No dashboard-grid-of-cards clutter. This is an analysis tool, not a BI dashboard — the page should feel like a single focused report, one clear verdict at the top, evidence underneath.
- No generic AI-generated aesthetic: no purple-to-blue gradients, no glassmorphism, no gradient blobs, no default shadcn look left untouched. Pick a restrained, confident palette (think: a serious analytics tool, not a SaaS landing page).
- The verdict card is the single most important visual element on any results page — it should be the first thing seen, in plain language, before any chart or p-value.
- Every statistical term (p-value, credible interval, FDR, power) gets a one-line plain-English tooltip on hover. Never assume the viewer knows the jargon — the whole point of this product is translating rigor into business language.
- Motion should be purposeful only (e.g., a distribution animating in once) — no decorative animation.
- Mobile-responsive is a nice-to-have, not a requirement; this is a desktop analysis tool.

---

## 8. Do's and Don'ts

**Do:**
- Validate every statistical method against the synthetic data generator with a known ground truth before trusting it on real data
- Use Welch's t-test by default, not Student's (don't assume equal variances)
- Show confidence/credible intervals everywhere, never just a point estimate
- State assumptions explicitly wherever a method relies on one (normality, parallel trends, independence)
- Keep backend statistical functions pure and unit-tested — this is the credibility core of the whole project, it must be correct
- Git micro-commit after each working phase with a clear message

**Don't:**
- Don't use p-values without also showing effect size and confidence interval — a p-value alone is not a business answer
- Don't let the user "peek" at a fixed-horizon test result without a clear warning, and don't silently apply sequential correction without telling them which method was used
- Don't reach for MCMC/PyMC for the Bayesian module — Beta-Binomial conjugacy is exact, faster, and free-tier-friendly; don't over-engineer
- Don't build user auth, multi-tenant projects, or any scope from section 4's "out of scope" list, even if it seems easy to add
- Don't ship a chart without a plain-English caption explaining what it shows and why it matters

---

## 9. Build Plan (phased — build and self-verify in this order)

**Phase 0 — Scaffold**
Initialize the Next.js frontend and FastAPI backend as separate services in one repo (or monorepo structure), set up Neon Postgres connection, confirm both deploy to Vercel/Render on an empty "hello world" route before writing any real logic.

**Phase 1 — Synthetic data generator + classical testing**
Build the synthetic data generator UI and backend endpoint. Build the two-proportion z-test and Welch's t-test. Verify: generate data with a known true effect of exactly 0%, confirm the test correctly fails to reject the null most of the time (i.e., check the false-positive rate is close to the stated alpha across repeated runs).

**Phase 2 — Normality check + Mann-Whitney fallback + power analysis**
Add automatic normality detection and test recommendation. Add power analysis (both directions: required sample size, and achieved power). Verify against textbook power-analysis examples with known answers.

**Phase 3 — Sequential testing**
Implement the peeking-safe method and the side-by-side naive-vs-corrected comparison. Verify by simulating repeated daily peeking on null-effect synthetic data and showing the naive method's inflated false-positive rate versus the corrected method's controlled rate.

**Phase 4 — Bayesian Beta-Binomial module**
Implement posterior calculation, P(treatment > control), expected loss, credible intervals. Verify against a known closed-form example.

**Phase 5 — CSV upload path**
Wire up real file upload, column mapping, and validation, feeding into the same engine built in Phases 1–4.

**Phase 6 — Causal impact module**
Implement DiD and the lightweight counterfactual time-series method. Verify DiD against a hand-computed textbook example. State assumptions clearly in the UI output.

**Phase 7 — Multiple testing correction**
Implement Benjamini-Hochberg for multi-metric runs.

**Phase 8 — Verdict layer + persistence**
Build the plain-English verdict generator that wraps every module's output. Wire up Postgres persistence and shareable run links.

**Phase 9 — UI/UX polish pass**
Apply the design rules in section 7 across every screen. Add tooltips for every statistical term. Final responsive/deploy check on Vercel + Render.

---

## 10. Success Criteria / What This Should Prove on the CV

By the end, Ved should be able to say: "I built an experimentation and causal-impact analytics platform that implements classical hypothesis testing, sequential/peeking-safe testing, Bayesian inference, and causal inference (difference-in-differences and counterfactual time series) — and validated every method against synthetic data with known ground truth." That sentence, on a fresher BA's CV, reads differently from every other portfolio in the pile.

---

## 11. First Prompt for Claude Code

Copy the block below as the first message to Claude Code in the new project directory.

```
Read CausalLens-Master-Spec.md in full before doing anything else — it is
the single source of truth for this project's requirements, architecture,
UI/UX rules, dos and don'ts, and build plan.

Build this project by working through the phases in section 9, in order.
After each phase: verify it works correctly (including the specific
statistical sanity checks named in that phase), git commit with a clear
message, then move to the next phase without stopping to ask permission,
unless you hit a genuine blocker (missing credential, ambiguous
requirement not covered in the spec, or a failing verification you can't
resolve).

Start with Phase 0 now: scaffold the Next.js frontend and FastAPI backend,
connect Neon Postgres, and confirm both deploy successfully on an empty
route before writing any statistical logic. Ask me for the Neon connection
string and confirm the GitHub repo URL before you begin, then proceed
autonomously through the phases.
```
