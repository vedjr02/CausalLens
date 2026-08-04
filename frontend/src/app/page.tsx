"use client";

import { useEffect, useState } from "react";
import {
  apiFetch,
  type DbHealthResponse,
  type HealthResponse,
} from "@/lib/api";

type Status = "checking" | "ok" | "down";

interface SystemState {
  api: Status;
  db: Status;
  apiDetail: string;
  dbDetail: string;
}

const INITIAL: SystemState = {
  api: "checking",
  db: "checking",
  apiDetail: "",
  dbDetail: "",
};

export default function Home() {
  const [state, setState] = useState<SystemState>(INITIAL);

  useEffect(() => {
    let cancelled = false;

    async function check() {
      let api: Status = "down";
      let apiDetail = "Not reachable";
      try {
        const health = await apiFetch<HealthResponse>("/health");
        api = health.status === "ok" ? "ok" : "down";
        apiDetail = health.environment;
      } catch (error) {
        apiDetail = error instanceof Error ? error.message : "Not reachable";
      }

      let db: Status = "down";
      let dbDetail = "Not reachable";
      try {
        const dbHealth = await apiFetch<DbHealthResponse>("/health/db");
        db = dbHealth.connected ? "ok" : "down";
        dbDetail = dbHealth.connected
          ? (dbHealth.server?.split(" ").slice(0, 2).join(" ") ?? "Connected")
          : (dbHealth.detail ?? "Not connected");
      } catch (error) {
        dbDetail = error instanceof Error ? error.message : "Not reachable";
      }

      if (!cancelled) setState({ api, db, apiDetail, dbDetail });
    }

    void check();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main className="mx-auto flex min-h-screen max-w-report flex-col justify-center px-8 py-24">
      <p className="text-xs uppercase tracking-[0.18em] text-ink-faint">
        CausalLens
      </p>

      <h1 className="mt-5 max-w-2xl text-4xl font-medium leading-[1.15] tracking-tight">
        Is that difference real, or did you get lucky?
      </h1>

      <p className="mt-5 max-w-xl text-[15px] leading-relaxed text-ink-muted">
        An experimentation and causal-impact tool. It runs the statistics
        properly &mdash; then tells you what they mean in plain English.
      </p>

      <div className="mt-14 border-t border-rule pt-6">
        <p className="text-xs uppercase tracking-[0.14em] text-ink-faint">
          System status
        </p>
        <dl className="mt-4">
          <StatusRow
            label="Analysis engine"
            status={state.api}
            detail={state.apiDetail}
          />
          <StatusRow
            label="Database"
            status={state.db}
            detail={state.dbDetail}
          />
        </dl>
      </div>

      <p className="mt-14 text-[13px] text-ink-faint">
        Phase 0 &mdash; scaffold. Statistical modules land in the phases that
        follow.
      </p>
    </main>
  );
}

function StatusRow({
  label,
  status,
  detail,
}: {
  label: string;
  status: Status;
  detail: string;
}) {
  const tone =
    status === "ok"
      ? "bg-positive"
      : status === "down"
        ? "bg-negative"
        : "bg-ink-faint";

  return (
    <div className="flex items-baseline justify-between gap-6 border-b border-rule py-3 last:border-b-0">
      <dt className="flex items-center gap-2.5 text-[15px]">
        <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${tone}`} />
        {label}
      </dt>
      <dd className="tnum truncate text-right text-[13px] text-ink-muted">
        {status === "checking" ? "Checking…" : detail}
      </dd>
    </div>
  );
}
