"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { TopNav } from "@/components/topnav";
import { Badge, EmptyState, ErrorBanner, Panel, Row, Stat } from "@/components/ui";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/auth";

const TABS = ["System Overview", "ABDM Trace", "Claims Oversight", "SOS Audit"] as const;
type Tab = (typeof TABS)[number];

type ServiceHealth = { name: string; status: string; ok: boolean };

export default function AdminHome() {
  const { session, ready } = useAuth();
  const [tab, setTab] = useState<Tab>("System Overview");
  const [err, setErr] = useState("");

  if (!ready) return null;
  if (!session || session.role !== "admin") {
    return (
      <div>
        <TopNav />
        <main className="max-w-md mx-auto px-6 py-20 text-center">
          <p className="font-display text-2xl">Administrators only.</p>
          <Link href="/login" className="btn mt-6">Sign in as admin</Link>
        </main>
      </div>
    );
  }

  return (
    <div>
      <TopNav />
      <main className="max-w-6xl mx-auto px-6 py-8">
        <div className="flex items-baseline justify-between">
          <h1 className="font-display text-3xl font-semibold">System oversight</h1>
          <span className="label-caps">NHCX / ABDM god view</span>
        </div>
        <ErrorBanner detail={err} />

        <div className="mt-6 flex gap-0 border-b border-ink overflow-x-auto">
          {TABS.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className="px-4 py-2.5 text-xs font-semibold uppercase tracking-widest whitespace-nowrap cursor-pointer"
              style={tab === t ? { background: "var(--ink)", color: "var(--paper)" } : { color: "var(--stone)" }}
            >
              {t}
            </button>
          ))}
        </div>

        <div className="mt-6">
          {tab === "System Overview" && <Overview />}
          {tab === "ABDM Trace" && <Trace />}
          {tab === "Claims Oversight" && <Oversight onErr={setErr} />}
          {tab === "SOS Audit" && <SosAudit />}
        </div>
      </main>
    </div>
  );
}

function Overview() {
  const { session } = useAuth();
  const [health, setHealth] = useState<ServiceHealth[]>([]);
  const [claims, setClaims] = useState<{ claims: { status: string; total: number }[] }>({ claims: [] });

  useEffect(() => {
    apiFetch<{ claims: { status: string; total: number }[] }>("/api/nhcx/claims", { token: session?.access_token })
      .then(setClaims)
      .catch(() => {});
  }, [session]);

  useEffect(() => {
    const names = ["identity", "records", "abdm", "nhcx", "sos"];
    const ports: Record<string, number> = { identity: 8001, records: 8002, abdm: 8003, nhcx: 8004, sos: 8005 };
    Promise.all(
      names.map(async (name) => {
        try {
          const r = await fetch(`http://localhost:${ports[name]}/health`);
          return { name, status: "online", ok: r.ok };
        } catch {
          return { name, status: "offline", ok: false };
        }
      })
    ).then(setHealth);
  }, []);

  const online = health.filter((h) => h.ok).length;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        <Stat label="Services online" value={`${online}/5`} accent={online === 5 ? "green" : "red"} />
        <Stat label="Claims tracked" value={claims.claims.length} />
        <Stat label="Claims approved" value={claims.claims.filter((c) => c.status === "APPROVED").length} />
        <Stat label="Claims rejected" value={claims.claims.filter((c) => c.status === "REJECTED").length} accent="red" />
      </div>

      <Panel title="Microservice health" flush>
        {health.map((h) => (
          <Row key={h.name}>
            <span className="mono text-sm">{h.name}-service</span>
            <Badge tone={h.ok ? "green" : "red"}>{h.status}</Badge>
            <span className="ml-auto label-caps">port {h.name === "identity" ? 8001 : h.name === "records" ? 8002 : h.name === "abdm" ? 8003 : h.name === "nhcx" ? 8004 : 8005}</span>
          </Row>
        ))}
      </Panel>
    </div>
  );
}

type LogRow = { id: number; ts: string; direction: string; endpoint: string; payload_snippet: string; status_code: number; latency_ms: number };

function Trace() {
  const { session } = useAuth();
  const [logs, setLogs] = useState<LogRow[]>([]);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    apiFetch<{ logs: LogRow[] }>("/api/abdm/logs", { token: session?.access_token })
      .then((r) => setLogs(r.logs))
      .catch(() => {});
  }, [session]);

  const shown = logs.filter((l) => l.endpoint.includes(filter) || l.payload_snippet.includes(filter));

  return (
    <Panel
      title="ABDM integration trace — every simulated gateway call, audited"
      right={<input className="input mono" style={{ width: 200, padding: "4px 8px" }} placeholder="filter..." value={filter} onChange={(e) => setFilter(e.target.value)} />}
      flush
    >
      {shown.length === 0 ? (
        <EmptyState text="No trace entries match." />
      ) : (
        shown.map((l) => (
          <Row key={l.id}>
            <Badge tone={l.direction === "IN" ? "green" : "ink"}>{l.direction}</Badge>
            <span className="mono text-xs">{l.endpoint}</span>
            <span className="mono text-[10px] text-stone truncate max-w-64 hidden md:inline">{l.payload_snippet}</span>
            <span className="ml-auto mono text-[10px]">{l.latency_ms}ms</span>
            <Badge tone={l.status_code < 400 ? "green" : "red"}>{l.status_code}</Badge>
          </Row>
        ))
      )}
    </Panel>
  );
}

function Oversight({ onErr }: { onErr: (s: string) => void }) {
  const { session } = useAuth();
  const [claims, setClaims] = useState<{ id: number; bill_id: number; patient_id: number; total: number; status: string; insurer_note: string; out_of_pocket: number }[]>([]);
  const [busyId, setBusyId] = useState<number | null>(null);

  const load = useCallback(() => {
    apiFetch<{ claims: typeof claims }>("/api/nhcx/claims", { token: session?.access_token })
      .then((r) => setClaims(r.claims))
      .catch(() => {});
  }, [session]);
  useEffect(load, [load]);

  async function adjudicate(id: number) {
    setBusyId(id);
    onErr("");
    try {
      await apiFetch(`/api/nhcx/claims/${id}/adjudicate`, { method: "POST", token: session?.access_token });
      load();
    } catch (e) {
      onErr((e as { detail: string }).detail);
    } finally {
      setBusyId(null);
    }
  }

  const pending = claims.filter((c) => c.status === "SUBMITTED");

  return (
    <Panel title={`Claims awaiting adjudication — ${pending.length}`} flush>
      {claims.length === 0 ? (
        <EmptyState text="No claims in the system." />
      ) : (
        claims.map((c) => (
          <Row key={c.id}>
            <span className="mono text-xs">#{c.id}</span>
            <span className="text-sm">Patient {c.patient_id}</span>
            <span className="font-display">₹{(c.total ?? 0).toLocaleString("en-IN")}</span>
            <Badge tone={c.status === "APPROVED" ? "green" : c.status === "REJECTED" ? "red" : "default"}>{c.status}</Badge>
            <span className="text-xs text-stone hidden md:inline truncate max-w-56">{c.insurer_note}</span>
            {c.status === "SUBMITTED" ? (
              <button className="btn ml-auto shrink-0" disabled={busyId === c.id} onClick={() => adjudicate(c.id)}>
                {busyId === c.id ? "Insurer processing..." : "Send to insurer"}
              </button>
            ) : (
              <span className="ml-auto mono text-[10px] text-stone shrink-0">
                {c.out_of_pocket > 0 ? `patient pays ₹${c.out_of_pocket.toLocaleString("en-IN")}` : "no out-of-pocket"}
              </span>
            )}
          </Row>
        ))
      )}
    </Panel>
  );
}

function SosAudit() {
  const { session } = useAuth();
  const [alerts, setAlerts] = useState<{ id: number; patient_name: string; trigger: string; location_label: string; email_status: string; created_at: string }[]>([]);

  useEffect(() => {
    apiFetch<{ alerts: typeof alerts }>("/api/sos/alerts", { token: session?.access_token })
      .then((r) => setAlerts(r.alerts))
      .catch(() => {});
  }, [session]);

  return (
    <Panel title="Every SOS alert ever dispatched" flush>
      {alerts.length === 0 ? (
        <EmptyState text="No alerts on record." />
      ) : (
        alerts.map((a) => (
          <Row key={a.id}>
            <span className="badge badge-red">{a.trigger}</span>
            <span className="text-sm font-medium">{a.patient_name}</span>
            <span className="text-xs text-stone truncate max-w-48">{a.location_label}</span>
            <Badge tone={a.email_status === "SENT" ? "green" : "default"}>email {a.email_status}</Badge>
            <span className="mono text-[10px] text-stone ml-auto">{new Date(a.created_at).toLocaleString()}</span>
          </Row>
        ))
      )}
    </Panel>
  );
}
