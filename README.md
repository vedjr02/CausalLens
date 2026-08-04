# CausalLens

**Is that difference real, or did you get lucky?**

An experimentation and causal-impact analytics tool. It runs the statistics
properly — classical hypothesis testing, peeking-safe sequential testing,
Bayesian inference, and causal inference — then translates the result into a
plain-English verdict a non-technical stakeholder can act on.

Every method is validated against a synthetic data generator with **known
ground truth**, so you can see the methods work rather than take them on faith.

## Layout

```
backend/     FastAPI + the statistical engine (scipy, statsmodels, numpy)
frontend/    Next.js 14 App Router, TypeScript, Tailwind, Recharts
render.yaml  Backend deploy config (Render, free tier)
```

## Running locally

Both services are defined in `.claude/launch.json`, or run them by hand:

**Backend** — needs [uv](https://docs.astral.sh/uv/); Python 3.12 is installed automatically.

```bash
cd backend && cp .env.example .env && uv sync && uv run uvicorn app.main:app --reload --port 8000
```

**Frontend**

```bash
cd frontend && cp .env.example .env.local && npm install && npm run dev
```

The app is then at `http://localhost:3000`, the API at `http://localhost:8000`
(interactive docs at `/docs`).

## Tests

```bash
cd backend && uv run pytest
```

The statistical functions are pure and unit-tested — that is the credibility
core of this project, so it has to be correct.

## Deploying

Not yet deployed. When it is:

- **Backend → Render.** `render.yaml` is ready; set `DATABASE_URL` and
  `CORS_ORIGINS` (must include the Vercel origin) as dashboard secrets.
- **Frontend → Vercel.** Set the project's *Root Directory* to `frontend` and
  `NEXT_PUBLIC_API_BASE_URL` to the Render URL.

## Status

| Phase | Scope | State |
| --- | --- | --- |
| 0 | Scaffold: Next.js, FastAPI, Neon Postgres | Done |
| 1 | Synthetic generator, two-proportion z-test, Welch's t-test | — |
| 2 | Normality check, Mann-Whitney fallback, power analysis | — |
| 3 | Sequential testing / peeking correction | — |
| 4 | Bayesian Beta-Binomial | — |
| 5 | CSV upload | — |
| 6 | Causal impact: DiD + counterfactual time series | — |
| 7 | Benjamini-Hochberg correction | — |
| 8 | Verdict layer + persistence | — |
| 9 | UI/UX polish | — |
