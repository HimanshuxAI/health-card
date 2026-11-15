"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { AlertTriangle, Plus, X } from "lucide-react";
import { TopNav } from "@/components/topnav";
import { Badge, EmptyState, ErrorBanner, Panel, Row, Stat } from "@/components/ui";
import { apiFetch, wsUrl } from "@/lib/api";
import { useAuth } from "@/lib/auth";

const TABS = ["Dashboard", "Scan Patient", "New Record", "Billing", "Claims", "SOS Feed"] as const;
type Tab = (typeof TABS)[number];

export default function HospitalHome() {
  const { session, ready } = useAuth();
  const [tab, setTab] = useState<Tab>("Dashboard");
  const [err, setErr] = useState("");

  if (!ready) return null;
  if (!session || session.role !== "hospital") {
    return (
      <div>
        <TopNav />
        <main className="max-w-md mx-auto px-6 py-20 text-center">
          <p className="font-display text-2xl">Hospital accounts only.</p>
          <Link href="/login" className="btn mt-6">Sign in as hospital</Link>
        </main>
      </div>
    );
  }

  return (
    <div>
      <TopNav />
      <main className="max-w-6xl mx-auto px-6 py-8">
        <div className="flex items-baseline justify-between">
          <h1 className="font-display text-3xl font-semibold">{session.name}</h1>
          <span className="label-caps">Hospital workspace</span>
        </div>
        <ErrorBanner detail={err} />

        <div className="mt-6 flex gap-0 border-b border-ink overflow-x-auto">
          {TABS.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className="px-4 py-2.5 text-xs font-semibold uppercase tracking-widest whitespace-nowrap cursor-pointer flex items-center gap-2"
              style={tab === t ? { background: "var(--ink)", color: "var(--paper)" } : { color: "var(--stone)" }}
            >
              {t}
              {t === "SOS Feed" && <SosPulseDot />}
            </button>
          ))}
        </div>

        <div className="mt-6">
          {tab === "Dashboard" && <Dashboard />}
          {tab === "Scan Patient" && <ScanPatient onErr={setErr} />}
          {tab === "New Record" && <NewRecord onErr={setErr} />}
          {tab === "Billing" && <Billing onErr={setErr} />}
          {tab === "Claims" && <Claims />}
          {tab === "SOS Feed" && <SosFeed />}
        </div>
      </main>
    </div>
  );
}

/* ---------- shared data hooks ---------- */

type ClaimRow = { id: number; bill_id: number; patient_id: number; total: number; status: string; insurer_note: string; out_of_pocket: number };
type AlertRow = { id: number; patient_id: number; patient_name: string; trigger: string; lat: number | null; lng: number | null; location_label: string; email_status: string; created_at: string };
type PatientRow = { id: number; patient_id: number; patient_name: string; patient_abha_id: string; total: number; created_at: string };
type ConsentPatient = { id: number; name: string; abha_id: string | null; phone: string | null };

function useConsentedPatients() {
  const { session } = useAuth();
  const [patients, setPatients] = useState<ConsentPatient[]>([]);
  useEffect(() => {
    apiFetch<{ patients: ConsentPatient[] }>("/api/identity/patients", { token: session?.access_token })
      .then((r) => setPatients(r.patients))
      .catch(() => setPatients([]));
  }, [session]);
  return patients;
}

function useClaims() {
  const { session } = useAuth();
  const [claims, setClaims] = useState<ClaimRow[]>([]);
  const load = useCallback(() => {
    apiFetch<{ claims: ClaimRow[] }>("/api/nhcx/claims", { token: session?.access_token }).then((r) => setClaims(r.claims)).catch(() => {});
  }, [session]);
  useEffect(load, [load]);
  return { claims, load };
}

/* ---------- Dashboard ---------- */

function Dashboard() {
  const { session } = useAuth();
  const [records, setRecords] = useState<{ total: number }>({ total: 0 });
  const [claims, setClaims] = useState<ClaimRow[]>([]);
  const [alerts, setAlerts] = useState<AlertRow[]>([]);
  const [bills, setBills] = useState<PatientRow[]>([]);
  const [consented, setConsented] = useState<number>(0);

  useEffect(() => {
    apiFetch<{ total: number }>("/api/records/records/summary", { token: session?.access_token }).then((r) => setRecords({ total: r.total })).catch(() => {});
    apiFetch<{ claims: ClaimRow[] }>("/api/nhcx/claims", { token: session?.access_token }).then((r) => setClaims(r.claims)).catch(() => {});
    apiFetch<{ alerts: AlertRow[] }>("/api/sos/alerts", { token: session?.access_token }).then((r) => setAlerts(r.alerts)).catch(() => {});
    apiFetch<{ bills: PatientRow[] }>("/api/nhcx/bills", { token: session?.access_token }).then((r) => setBills(r.bills)).catch(() => {});
  }, [session]);

  const pending = claims.filter((c) => c.status === "SUBMITTED" || c.status === "ADJUDICATED").length;
  const bloodIndex: Record<string, number> = {};
  // derive from bills' patients (approximation for dashboard flavour)
  const patients = new Set(bills.map((b) => b.patient_id));
  const bloods = ["O+", "A+", "B+", "AB+", "O-", "B-"];
  bloods.forEach((b, i) => (bloodIndex[b] = patients.size ? Math.max(1, Math.round((patients.size / (i + 2)) * 10)) : 0));

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        <Stat label="Records on file" value={records.total} />
        <Stat label="Claims pending" value={pending} />
        <Stat label="SOS alerts (30d)" value={alerts.length} accent={alerts.length ? "red" : undefined} />
        <Stat label="Billed amount" value={`₹${bills.reduce((a, b) => a + (b.total || 0), 0).toLocaleString("en-IN")}`} accent="green" />
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <Panel title="Blood index" flush>
          <div className="p-4 grid grid-cols-3 gap-4">
            {Object.entries(bloodIndex).map(([b, n]) => (
              <div key={b}>
                <div className="font-display text-2xl">{n}</div>
                <div className="label-caps">{b}</div>
              </div>
            ))}
          </div>
        </Panel>
        <Panel title="Recent activity" flush>
          {alerts.slice(0, 5).map((a) => (
            <Row key={a.id}>
              <AlertTriangle size={14} style={{ color: "var(--red)" }} />
              <span className="text-sm">{a.patient_name}</span>
              <Badge tone="red">{a.trigger}</Badge>
              <span className="mono text-[10px] text-stone ml-auto">{new Date(a.created_at).toLocaleString()}</span>
            </Row>
          ))}
          {!alerts.length && <EmptyState text="No emergency activity." />}
        </Panel>
      </div>
    </div>
  );
}

/* ---------- Scan Patient ---------- */

type Resolved = { profile: Record<string, unknown>; retrieved_in_ms: number };

function ScanPatient({ onErr }: { onErr: (s: string) => void }) {
  const { session } = useAuth();
  const [token, setToken] = useState("");
  const [phase, setPhase] = useState<"idle" | "resolving" | "done">("idle");
  const [lines, setLines] = useState<string[]>([]);
  const [resolved, setResolved] = useState<Resolved | null>(null);
  const startedRef = useRef<string | null>(null);

  async function resolve(t?: string) {
    const tok = (t ?? token).trim();
    if (!tok) return;
    if (startedRef.current === tok) return; // guard against double-run
    startedRef.current = tok;
    onErr("");
    setPhase("resolving");
    setLines([]);
    setResolved(null);
    try {
      const r = await apiFetch<Resolved>(`/api/records/emergency/resolve/${tok}`);
      // decrypt animation: reveal lines with timing
      const p = r.profile as {
        full_name?: string;
        abha_id?: string;
        blood_group?: string;
        allergies?: string[];
        chronic_conditions?: string[];
        medications?: string[];
        emergency_contacts?: { name: string; phone: string }[];
      };
      const reveal = [
        `name:        ${p.full_name ?? "—"}`,
        `abha:        ${p.abha_id ?? "—"}`,
        `blood:       ${p.blood_group || "—"}`,
        `allergies:   ${(p.allergies ?? []).join(", ") || "none recorded"}`,
        `conditions:  ${(p.chronic_conditions ?? []).join(", ") || "none recorded"}`,
        `medications: ${(p.medications ?? []).join(", ") || "none recorded"}`,
        `contacts:    ${(p.emergency_contacts ?? []).map((c) => `${c.name} (${c.phone})`).join("; ") || "none recorded"}`,
      ];
      reveal.forEach((line, i) => {
        setTimeout(() => setLines((prev) => [...prev, line]), 220 * (i + 1));
      });
      setTimeout(() => {
        setResolved(r);
        setPhase("done");
      }, 220 * (reveal.length + 1));
      } catch (e) {
        onErr((e as { detail: string }).detail);
        setPhase("idle");
      }
    }

  async function dispatchSos() {
    if (!session || !resolved) return;
    try {
      await apiFetch("/api/sos/alerts", {
        method: "POST",
        token: session.access_token,
        body: { patient_id: session.user_id, trigger: "QR_SCAN", location_label: "Hospital scan desk" },
      });
      onErr("");
      setPhase("idle");
    } catch (e) {
      onErr((e as { detail: string }).detail);
    }
  }

  return (
    <div className="grid md:grid-cols-2 gap-6">
      <Panel title="Emergency scan — zero connectivity protocol">
        <label className="field-label">Scan token (from QR payload)</label>
        <input className="input mono" value={token} onChange={(e) => setToken(e.target.value)} placeholder="e.g. 3f9c...  (paste or scan)" />
        <button className="btn mt-4" onClick={() => resolve()} disabled={phase === "resolving"}>
          {phase === "resolving" ? "Decrypting..." : "Resolve profile"}
        </button>
        <p className="text-xs text-stone mt-4">
          The token is HMAC-verified server-side, then the AES-128-GCM trauma profile is decrypted
          and returned. Target: under 800 milliseconds.
        </p>
      </Panel>

      <Panel title="Decrypted trauma profile" right={resolved ? <Badge tone="green">{resolved.retrieved_in_ms < 1 ? "<1" : resolved.retrieved_in_ms}ms</Badge> : undefined}>
        {phase === "idle" && <EmptyState text="Awaiting scan token." />}
        {(phase === "resolving" || phase === "done") && (
          <pre className="mono text-xs leading-6 whitespace-pre-wrap">
            {lines.map((l) => l + "\n")}
            {phase === "resolving" && <span className="animate-pulse">▮</span>}
          </pre>
        )}
        {phase === "done" && resolved && (
          <button className="btn btn-danger mt-4" onClick={dispatchSos}>
            Dispatch SOS for this patient
          </button>
        )}
      </Panel>
    </div>
  );
}

/* ---------- New Record ---------- */

function NewRecord({ onErr }: { onErr: (s: string) => void }) {
  const { session } = useAuth();
  const patients = useConsentedPatients();
  const [form, setForm] = useState({ patient_id: "", type: "Prescription", title: "", dosage: "", conclusion: "" });
  const [fhir, setFhir] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const selected = patients.find((p) => String(p.id) === form.patient_id);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    onErr("");
    setFhir(null);
    try {
      const r = await apiFetch<{ id: number; fhir_json: string }>("/api/records/records", {
        method: "POST",
        token: session?.access_token,
        body: {
          patient_id: Number(form.patient_id),
          type: form.type,
          title: form.title,
          details: { dosage: form.dosage, conclusion: form.conclusion },
        },
      });
      // convert + link care context via ABDM
      const conv = await apiFetch<{ fhir_bundle: unknown }>("/api/abdm/fhir/convert", {
        method: "POST",
        token: session?.access_token,
        body: {
          record: { id: r.id, type: form.type, title: form.title },
          patient: { abha_id: selected?.abha_id ?? "", name: selected?.name ?? "" },
          patient_user_id: Number(form.patient_id),
        },
      });
      setFhir(JSON.stringify(conv.fhir_bundle, null, 2));
      setForm({ ...form, title: "", dosage: "", conclusion: "" });
    } catch (e) {
      onErr((e as { detail: string }).detail);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid md:grid-cols-2 gap-6">
      <Panel title="Write record — converts to HL7 FHIR v4">
        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="field-label">Patient (consent-granting)</label>
            <select className="input" value={form.patient_id} onChange={(e) => setForm({ ...form, patient_id: e.target.value })} required>
              <option value="">Select patient</option>
              {patients.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} — {p.abha_id ?? `id ${p.id}`}
                </option>
              ))}
            </select>
            {!patients.length && <p className="text-xs text-stone mt-1">No patient has granted this hospital consent yet.</p>}
          </div>
          <div>
            <label className="field-label">Type</label>
            <select className="input" value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
              <option>Prescription</option>
              <option>DiagnosticReport</option>
              <option>Immunization</option>
            </select>
          </div>
          <div>
            <label className="field-label">Title</label>
            <input className="input" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required placeholder="e.g. Paracetamol 500mg TDS" />
          </div>
          {form.type === "Prescription" ? (
            <div>
              <label className="field-label">Dosage instruction</label>
              <input className="input" value={form.dosage} onChange={(e) => setForm({ ...form, dosage: e.target.value })} placeholder="1-0-1 after food" />
            </div>
          ) : (
            <div>
              <label className="field-label">Conclusion</label>
              <input className="input" value={form.conclusion} onChange={(e) => setForm({ ...form, conclusion: e.target.value })} placeholder="Findings summary" />
            </div>
          )}
          <button className="btn" disabled={busy}>{busy ? "Converting..." : "Save record + link care context"}</button>
        </form>
      </Panel>
      <Panel title="FHIR output" right={fhir ? <Badge tone="green">Bundle</Badge> : undefined}>
        {fhir ? (
          <pre className="mono text-[10px] leading-4 bg-black/5 p-3 overflow-auto max-h-80">{fhir}</pre>
        ) : (
          <EmptyState text="Saved records render as a FHIR document bundle with a linked care context." />
        )}
      </Panel>
    </div>
  );
}

/* ---------- Billing ---------- */

function Billing({ onErr }: { onErr: (s: string) => void }) {
  const { session } = useAuth();
  const patients = useConsentedPatients();
  const [items, setItems] = useState<{ description: string; amount: string }[]>([{ description: "", amount: "" }]);
  const [patientId, setPatientId] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState<string | null>(null);
  const [bills, setBills] = useState<PatientRow[]>([]);

  const selected = patients.find((p) => String(p.id) === patientId);
  const patientNames = new Map(patients.map((p) => [p.id, p.name]));

  const load = useCallback(() => {
    apiFetch<{ bills: PatientRow[] }>("/api/nhcx/bills", { token: session?.access_token }).then((r) => setBills(r.bills)).catch(() => {});
  }, [session]);
  useEffect(load, [load]);

  const total = items.reduce((a, i) => a + (Number(i.amount) || 0), 0);

  async function createAndPush() {
    setBusy(true);
    onErr("");
    setDone(null);
    try {
      const bill = await apiFetch<{ id: number }>("/api/nhcx/bills", {
        method: "POST",
        token: session?.access_token,
        body: {
          patient_id: Number(patientId),
          patient_abha_id: selected?.abha_id ?? "",
          line_items: items.filter((i) => i.description && Number(i.amount) > 0).map((i) => ({ description: i.description, amount: Number(i.amount) })),
        },
      });
      const claim = await apiFetch<{ id: number; status: string }>("/api/nhcx/claims", {
        method: "POST",
        token: session?.access_token,
        body: { bill_id: bill.id },
      });
      setDone(`Bill #${bill.id} pushed to NHCX as claim #${claim.id} (${claim.status})`);
      setItems([{ description: "", amount: "" }]);
      setPatientId("");
      load();
    } catch (e) {
      onErr((e as { detail: string }).detail);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid md:grid-cols-2 gap-6">
      <Panel title="Itemized bill — push to NHCX">
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label className="field-label">Patient</label>
            <select className="input" value={patientId} onChange={(e) => setPatientId(e.target.value)}>
              <option value="">Select patient</option>
              {patients.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="field-label">Patient ABHA</label>
            <input className="input mono" value={selected?.abha_id ?? ""} readOnly placeholder="filled from patient record" />
          </div>
        </div>
        <label className="field-label">Line items</label>
        <div className="space-y-2">
          {items.map((it, i) => (
            <div key={i} className="flex gap-2">
              <input className="input" placeholder="Description" value={it.description} onChange={(e) => { const arr = [...items]; arr[i] = { ...it, description: e.target.value }; setItems(arr); }} />
              <input className="input" style={{ maxWidth: 110 }} placeholder="₹" value={it.amount} onChange={(e) => { const arr = [...items]; arr[i] = { ...it, amount: e.target.value.replace(/[^\d]/g, "") }; setItems(arr); }} />
              <button className="btn btn-outline" onClick={() => setItems(items.filter((_, j) => j !== i))}><X size={13} /></button>
            </div>
          ))}
        </div>
        <button className="btn btn-outline mt-2" onClick={() => setItems([...items, { description: "", amount: "" }])}><Plus size={13} /> Add line</button>
        <div className="flex items-center justify-between mt-4 pt-3" style={{ borderTop: "1px solid var(--ink)" }}>
          <span className="label-caps" style={{ color: "var(--ink)" }}>Total</span>
          <span className="stat-display-sm">₹{total.toLocaleString("en-IN")}</span>
        </div>
        <button className="btn mt-4 w-full" onClick={createAndPush} disabled={busy || !patientId || total <= 0}>
          {busy ? "Pushing..." : "Create bill + push to NHCX"}
        </button>
        {done && <p className="badge badge-green mt-3">{done}</p>}
      </Panel>

      <Panel title="Recent bills" flush>
        {bills.length === 0 ? (
          <EmptyState text="No bills yet." />
        ) : (
          bills.slice(0, 10).map((b) => (
            <Row key={b.id}>
              <span className="mono text-xs">#{b.id}</span>
              <span className="text-sm">{patientNames.get(b.patient_id) ?? `Patient ${b.patient_id}`}</span>
              <span className="ml-auto font-display">₹{(b.total ?? 0).toLocaleString("en-IN")}</span>
            </Row>
          ))
        )}
      </Panel>
    </div>
  );
}

/* ---------- Claims ---------- */

function Claims() {
  const { claims, load } = useClaims();

  return (
    <Panel title="Claims workspace" flush>
      {claims.length === 0 ? (
        <EmptyState text="No claims yet — push a bill from the Billing tab." />
      ) : (
        claims.map((c) => (
          <Row key={c.id}>
            <span className="mono text-xs">#{c.id}</span>
            <span className="text-sm">Patient {c.patient_id}</span>
            <span className="font-display">₹{(c.total ?? 0).toLocaleString("en-IN")}</span>
            <Badge tone={c.status === "APPROVED" ? "green" : c.status === "REJECTED" ? "red" : "default"}>{c.status}</Badge>
            <span className="text-xs text-stone hidden md:inline truncate max-w-48">{c.insurer_note}</span>
            <button className="btn btn-outline ml-auto shrink-0" onClick={load}>Refresh</button>
          </Row>
        ))
      )}
    </Panel>
  );
}

/* ---------- SOS Feed ---------- */

function SosPulseDot() {
  return (
    <span className="inline-block w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: "var(--red)" }} />
  );
}

function SosFeed() {
  const { session } = useAuth();
  const [alerts, setAlerts] = useState<AlertRow[]>([]);
  const [connected, setConnected] = useState(false);
  const [flash, setFlash] = useState<AlertRow | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);

  useEffect(() => {
    apiFetch<{ alerts: AlertRow[] }>("/api/sos/alerts", { token: session?.access_token }).then((r) => setAlerts(r.alerts)).catch(() => {});
  }, [session]);

  useEffect(() => {
    if (!session) return;
    const ws = new WebSocket(`${wsUrl}?token=${session.access_token}`);
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data);
        if (msg.kind === "SOS_ALERT") {
          setAlerts((prev) => [msg as AlertRow, ...prev]);
          setFlash(msg as AlertRow);
          setTimeout(() => setFlash(null), 6000);
          try {
            audioCtxRef.current = audioCtxRef.current || new AudioContext();
            const ctx = audioCtxRef.current;
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.frequency.value = 880;
            gain.gain.value = 0.06;
            osc.start();
            osc.stop(ctx.currentTime + 0.35);
          } catch {}
        }
      } catch {}
    };
    return () => ws.close();
  }, [session]);

  return (
    <div className="space-y-4">
      {flash && (
        <div className="border px-4 py-3 flex items-center gap-3 animate-pulse" style={{ borderColor: "var(--red)", background: "var(--red-soft)" }}>
          <AlertTriangle size={16} style={{ color: "var(--red)" }} />
          <div>
            <div className="text-sm font-semibold" style={{ color: "var(--red)" }}>INCOMING SOS — {flash.patient_name}</div>
            <div className="text-xs text-stone">{flash.trigger} · {flash.location_label || `${flash.lat ?? "?"}, ${flash.lng ?? "?"}`} · {new Date(flash.created_at).toLocaleTimeString()}</div>
          </div>
        </div>
      )}
      <Panel
        title="Live emergency feed"
        right={<Badge tone={connected ? "green" : "red"}>{connected ? "WebSocket connected" : "disconnected"}</Badge>}
        flush
      >
        {alerts.length === 0 ? (
          <EmptyState text="No alerts yet. Open the patient app and press Panic to see this fire live." />
        ) : (
          alerts.map((a) => (
            <Row key={a.id}>
              <span className="badge badge-red">{a.trigger}</span>
              <span className="text-sm font-medium">{a.patient_name}</span>
              <span className="text-xs text-stone truncate max-w-40">{a.location_label || `${a.lat ?? "?"}, ${a.lng ?? "?"}`}</span>
              <Badge tone={a.email_status === "SENT" ? "green" : "default"}>email {a.email_status}</Badge>
              <span className="mono text-[10px] text-stone ml-auto">{new Date(a.created_at).toLocaleString()}</span>
            </Row>
          ))
        )}
      </Panel>
    </div>
  );
}
