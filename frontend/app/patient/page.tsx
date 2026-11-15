"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { QRCodeSVG } from "qrcode.react";
import { AlertTriangle, PhoneCall, Plus, X } from "lucide-react";
import { TopNav } from "@/components/topnav";
import { Badge, EmptyState, ErrorBanner, Panel, Row } from "@/components/ui";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/auth";

type Profile = {
  full_name: string;
  abha_id: string | null;
  blood_group: string;
  allergies: string[];
  chronic_conditions: string[];
  medications: string[];
  emergency_contacts: { name: string; phone: string; relation: string; email?: string }[];
};

type RecordRow = {
  id: number;
  type: string;
  title: string;
  fhir_json: string;
  created_at: string;
};

type ClaimRow = {
  id: number;
  bill_id: number;
  total: number;
  status: string;
  insurer_note: string;
  out_of_pocket: number;
  created_at: string;
};

type ConsentRow = {
  id: number;
  hospital_id: number;
  hospital_name?: string | null;
  scope: string;
  granted_at: string;
};

const TABS = ["My Card", "Emergency Profile", "Records", "Consents", "Billing & Claims"] as const;
type Tab = (typeof TABS)[number];

export default function PatientHome() {
  const { session, ready, logout } = useAuth();
  const [tab, setTab] = useState<Tab>("My Card");
  const [err, setErr] = useState("");

  if (!ready) return null;
  if (!session || session.role !== "patient") {
    return (
      <div>
        <TopNav />
        <main className="max-w-md mx-auto px-6 py-20 text-center">
          <p className="font-display text-2xl">Patients only.</p>
          <Link href="/login" className="btn mt-6">Sign in as patient</Link>
        </main>
      </div>
    );
  }

  return (
    <div>
      <TopNav />
      <main className="max-w-6xl mx-auto px-6 py-8">
        <div className="flex items-baseline justify-between">
          <h1 className="font-display text-3xl font-semibold">Patient records</h1>
          <span className="mono text-xs text-stone">{session.name}</span>
        </div>
        <ErrorBanner detail={err} />

        {/* tab strip */}
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
          {tab === "My Card" && <MyCard onErr={setErr} />}
          {tab === "Emergency Profile" && <EmergencyProfile onErr={setErr} />}
          {tab === "Records" && <Records />}
          {tab === "Consents" && <Consents />}
          {tab === "Billing & Claims" && <BillingClaims />}
        </div>
      </main>
    </div>
  );
}

/* ---------------- My Card ---------------- */

function MyCard({ onErr }: { onErr: (s: string) => void }) {
  const { session } = useAuth();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [qr, setQr] = useState<{ token: string } | null>(null);
  const [sosState, setSosState] = useState<"idle" | "sending" | "sent">("idle");

  useEffect(() => {
    apiFetch<Profile>("/api/records/emergency/profile", { token: session?.access_token })
      .then(setProfile)
      .catch(() => {});
    apiFetch<{ token: string }>("/api/records/emergency/qr", { method: "POST", token: session?.access_token })
      .then(setQr)
      .catch(() => {});
  }, [session]);

  async function panic() {
    if (!session || sosState !== "idle") return;
    setSosState("sending");
    onErr("");
    let lat: number | undefined;
    let lng: number | undefined;
    try {
      const pos = await new Promise<GeolocationPosition>((res, rej) =>
        navigator.geolocation.getCurrentPosition(res, rej, { timeout: 4000 })
      );
      lat = pos.coords.latitude;
      lng = pos.coords.longitude;
    } catch {}
    try {
      await apiFetch("/api/sos/alerts", {
        method: "POST",
        token: session.access_token,
        body: { patient_id: session.user_id, trigger: "PANIC", lat, lng, location_label: "Panic button" },
      });
      setSosState("sent");
    } catch (e) {
      onErr((e as { detail: string }).detail);
      setSosState("idle");
    }
  }

  const scanUrl = qr ? `${typeof window !== "undefined" ? window.location.origin : ""}/scan?t=${qr.token}` : "";

  return (
    <div className="grid md:grid-cols-[1fr_320px] gap-8">
      {/* black hero card */}
      <div>
        <div className="relative overflow-hidden" style={{ background: "var(--ink)", color: "var(--paper)" }}>
          <div className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <div className="label-caps" style={{ color: "#a8a29e" }}>Digital health card</div>
                <div className="font-display text-2xl font-semibold mt-1">{profile?.full_name || session?.name}</div>
                <div className="mono text-xs mt-1" style={{ color: "#a8a29e" }}>
                  ABHA {profile?.abha_id || "— link pending —"}
                </div>
              </div>
              <Badge tone="ink" >Emergency Ready</Badge>
            </div>
            <div className="flex gap-2 mt-5 flex-wrap">
              {profile?.blood_group && <span className="badge" style={{ background: "var(--paper)", color: "var(--ink)" }}>Blood {profile.blood_group}</span>}
              {profile?.allergies?.length
                ? profile.allergies.map((a) => (
                    <span key={a} className="badge" style={{ background: "#fdeaea", color: "var(--red)", borderColor: "var(--red)" }}>
                      Allergy: {a}
                    </span>
                  ))
                : !profile && <span className="badge" style={{ borderColor: "#57534e", color: "#a8a29e" }}>Profile loading</span>}
              {profile && !profile.allergies?.length && (
                <span className="badge" style={{ borderColor: "#57534e", color: "#a8a29e" }}>No known allergies</span>
              )}
            </div>
          </div>
        </div>

        {/* panic strip */}
        <div className="mt-4 flex items-center justify-between border border-ink px-4 py-3" style={{ background: "var(--red-soft)" }}>
          <div>
            <div className="text-sm font-semibold" style={{ color: "var(--red)" }}>Emergency SOS</div>
            <div className="text-xs text-stone">Alerts every hospital dashboard and emails your contacts with your location.</div>
          </div>
          <button className="btn btn-danger" onClick={panic} disabled={sosState !== "idle"}>
            {sosState === "idle" ? "Panic" : sosState === "sending" ? "Dispatching" : "Dispatched"}
          </button>
        </div>

        {/* contacts */}
        <Panel title="Emergency contacts" flush>
          {profile?.emergency_contacts?.length ? (
            profile.emergency_contacts.map((c, i) => (
              <Row key={i}>
                <PhoneCall size={14} />
                <span className="text-sm font-medium">{c.name}</span>
                <span className="text-xs text-stone">{c.relation}</span>
                <span className="mono text-xs ml-auto">{c.phone}</span>
              </Row>
            ))
          ) : (
            <EmptyState text="No emergency contacts yet — add them in the Emergency Profile tab." />
          )}
        </Panel>
      </div>

      {/* QR column */}
      <div className="panel p-5 text-center">
        <div className="label-caps">Scan for emergency profile</div>
        <div className="mt-4 flex justify-center">
          {qr ? <QRCodeSVG value={scanUrl} size={190} bgColor="#ffffff" fgColor="#1c1917" /> : <div className="h-[190px] flex items-center text-xs text-stone">Generating token...</div>}
        </div>
        <p className="text-xs text-stone mt-4 leading-relaxed">
          Anyone with this QR — a paramedic, a stranger, a doctor — can open your trauma profile
          without an account. Regenerate any time to invalidate old prints.
        </p>
        {qr && <div className="mono text-[10px] text-stone mt-3 break-all">{qr.token}</div>}
      </div>
    </div>
  );
}

/* ---------------- Emergency Profile ---------------- */

function StringListEditor({
  label,
  items,
  onChange,
  placeholder,
}: {
  label: string;
  items: string[];
  onChange: (v: string[]) => void;
  placeholder: string;
}) {
  const [draft, setDraft] = useState("");
  return (
    <div>
      <label className="field-label">{label}</label>
      <div className="flex gap-2 flex-wrap mb-2">
        {items.map((it) => (
          <span key={it} className="badge">
            {it}
            <button onClick={() => onChange(items.filter((x) => x !== it))} className="cursor-pointer"><X size={10} /></button>
          </span>
        ))}
      </div>
      <div className="flex gap-2">
        <input className="input" value={draft} placeholder={placeholder} onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && draft.trim()) {
              e.preventDefault();
              onChange([...items, draft.trim()]);
              setDraft("");
            }
          }} />
        <button className="btn btn-outline" type="button" onClick={() => { if (draft.trim()) { onChange([...items, draft.trim()]); setDraft(""); } }}>
          <Plus size={13} />
        </button>
      </div>
    </div>
  );
}

function EmergencyProfile({ onErr }: { onErr: (s: string) => void }) {
  const { session } = useAuth();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    apiFetch<Profile>("/api/records/emergency/profile", { token: session?.access_token }).then(setProfile).catch(() => {});
  }, [session]);

  if (!profile) return <p className="text-sm text-stone">Loading profile...</p>;

  function upd(p: Partial<Profile>) {
    setProfile({ ...profile!, ...p });
    setSaved(false);
  }

  async function save() {
    setBusy(true);
    onErr("");
    try {
      await apiFetch("/api/records/emergency/profile", {
        method: "PUT",
        token: session?.access_token,
        body: {
          full_name: profile!.full_name,
          blood_group: profile!.blood_group,
          allergies: profile!.allergies,
          chronic_conditions: profile!.chronic_conditions,
          medications: profile!.medications,
          emergency_contacts: profile!.emergency_contacts,
        },
      });
      setSaved(true);
    } catch (e) {
      onErr((e as { detail: string }).detail);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-2xl">
      <Panel title="Emergency profile — encrypted at rest, shown when your card is scanned">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="field-label">Blood group</label>
            <select className="input" value={profile.blood_group} onChange={(e) => upd({ blood_group: e.target.value })}>
              <option value="">Select</option>
              {["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"].map((b) => <option key={b}>{b}</option>)}
            </select>
          </div>
          <div>
            <label className="field-label">Full name</label>
            <input className="input" value={profile.full_name} onChange={(e) => upd({ full_name: e.target.value })} />
          </div>
        </div>
        <div className="mt-4">
          <StringListEditor label="Severe drug allergies" items={profile.allergies} onChange={(v) => upd({ allergies: v })} placeholder="e.g. Penicillin" />
        </div>
        <div className="mt-4">
          <StringListEditor label="Chronic conditions" items={profile.chronic_conditions} onChange={(v) => upd({ chronic_conditions: v })} placeholder="e.g. Type 1 Diabetes" />
        </div>
        <div className="mt-4">
          <StringListEditor label="Current medications" items={profile.medications} onChange={(v) => upd({ medications: v })} placeholder="e.g. Insulin basal" />
        </div>

        <div className="mt-6">
          <label className="field-label">Emergency contacts</label>
          <div className="space-y-2">
            {profile.emergency_contacts.map((c, i) => (
              <div key={i} className="flex gap-2 items-center">
                <input className="input" value={c.name} placeholder="Name" onChange={(e) => { const arr = [...profile.emergency_contacts]; arr[i] = { ...c, name: e.target.value }; upd({ emergency_contacts: arr }); }} />
                <input className="input" value={c.phone} placeholder="Phone" onChange={(e) => { const arr = [...profile.emergency_contacts]; arr[i] = { ...c, phone: e.target.value }; upd({ emergency_contacts: arr }); }} />
                <input className="input" style={{ maxWidth: 120 }} value={c.relation} placeholder="Relation" onChange={(e) => { const arr = [...profile.emergency_contacts]; arr[i] = { ...c, relation: e.target.value }; upd({ emergency_contacts: arr }); }} />
                <button className="btn btn-outline" onClick={() => upd({ emergency_contacts: profile.emergency_contacts.filter((_, j) => j !== i) })}><X size={13} /></button>
              </div>
            ))}
          </div>
          <button
            className="btn btn-outline mt-2"
            onClick={() => upd({ emergency_contacts: [...profile.emergency_contacts, { name: "", phone: "", relation: "" }] })}
          >
            <Plus size={13} /> Add contact
          </button>
        </div>

        <div className="mt-6 flex items-center gap-4">
          <button className="btn" onClick={save} disabled={busy}>{busy ? "Encrypting..." : "Save & re-seal profile"}</button>
          {saved && <span className="badge badge-green">Saved — trauma profile re-sealed</span>}
        </div>
      </Panel>
    </div>
  );
}

/* ---------------- Records ---------------- */

function Records() {
  const { session } = useAuth();
  const [records, setRecords] = useState<RecordRow[]>([]);
  const [open, setOpen] = useState<number | null>(null);

  useEffect(() => {
    apiFetch<{ records: RecordRow[] }>("/api/records/records", { token: session?.access_token })
      .then((r) => setRecords(r.records))
      .catch(() => {});
  }, [session]);

  return (
    <Panel title={`Health records — ${records.length}`} flush>
      {records.length === 0 ? (
        <EmptyState text="No records yet. A hospital adds these when you visit." />
      ) : (
        records.map((r) => (
          <Row key={r.id}>
            <div className="w-32 shrink-0"><Badge>{r.type}</Badge></div>
            <div className="min-w-0">
              <div className="text-sm font-medium truncate">{r.title}</div>
              <div className="mono text-[10px] text-stone">{new Date(r.created_at).toLocaleString()}</div>
            </div>
            <button className="btn btn-outline ml-auto shrink-0" onClick={() => setOpen(open === r.id ? null : r.id)}>
              {open === r.id ? "Hide FHIR" : "View FHIR"}
            </button>
            {open === r.id && (
              <pre className="mono text-[10px] leading-4 bg-black/5 p-3 overflow-auto max-h-48 max-w-sm shrink-0">{JSON.stringify(JSON.parse(r.fhir_json), null, 2)}</pre>
            )}
          </Row>
        ))
      )}
    </Panel>
  );
}

/* ---------------- Consents ---------------- */

function Consents() {
  const { session } = useAuth();
  const [consents, setConsents] = useState<ConsentRow[]>([]);
  const [err, setErr] = useState("");

  const load = useCallback(() => {
    apiFetch<{ consents: ConsentRow[] }>("/api/identity/consents", { token: session?.access_token })
      .then((r) => setConsents(r.consents))
      .catch(() => {});
  }, [session]);

  useEffect(load, [load]);

  async function revoke(id: number) {
    try {
      await apiFetch(`/api/identity/consents/${id}/revoke`, { method: "POST", token: session?.access_token });
      load();
    } catch (e) {
      setErr((e as { detail: string }).detail);
    }
  }

  return (
    <div className="max-w-2xl">
      <ErrorBanner detail={err} />
      <Panel title="Hospital access (ABDM consent artifacts)" flush>
        {consents.length === 0 ? (
          <EmptyState text="No hospital currently holds access to your records." />
        ) : (
          consents.map((c) => (
            <Row key={c.id}>
              <div className="text-sm font-medium">{c.hospital_name ?? `Hospital #${c.hospital_id}`}</div>
              <Badge tone="green">{c.scope}</Badge>
              <span className="mono text-[10px] text-stone">granted {new Date(c.granted_at).toLocaleDateString()}</span>
              <button className="btn btn-outline ml-auto" onClick={() => revoke(c.id)}>Revoke</button>
            </Row>
          ))
        )}
      </Panel>
      <p className="text-xs text-stone mt-3">Consents are artifacts with an expiry. Revoking stops all future hospital reads immediately.</p>
    </div>
  );
}

/* ---------------- Billing & Claims ---------------- */

function BillingClaims() {
  const { session } = useAuth();
  const [claims, setClaims] = useState<ClaimRow[]>([]);

  useEffect(() => {
    apiFetch<{ claims: ClaimRow[] }>("/api/nhcx/claims", { token: session?.access_token })
      .then((r) => setClaims(r.claims))
      .catch(() => {});
  }, [session]);

  const STEPS = ["SUBMITTED", "ADJUDICATED", "APPROVED"];

  return (
    <Panel title="Insurance claims (NHCX)" flush>
      {claims.length === 0 ? (
        <EmptyState text="No claims yet. Your hospital pushes bills to NHCX." />
      ) : (
        claims.map((c) => {
          const rejected = c.status === "REJECTED";
          return (
            <Row key={c.id} >
              <div>
                <div className="text-sm font-medium">Claim #{c.id} — Bill #{c.bill_id}</div>
                <div className="text-xs text-stone">{c.insurer_note || "Awaiting insurer"}</div>
              </div>
              <div className="ml-auto text-right">
                <div className="font-display text-lg">₹{c.total.toLocaleString("en-IN")}</div>
                {c.out_of_pocket > 0 && <div className="text-xs" style={{ color: "var(--red)" }}>you pay ₹{c.out_of_pocket.toLocaleString("en-IN")}</div>}
                {c.out_of_pocket === 0 && c.status === "APPROVED" && <div className="text-xs" style={{ color: "var(--green)" }}>fully covered</div>}
              </div>
              <div className="flex gap-1">
                {rejected ? (
                  <Badge tone="red">Rejected</Badge>
                ) : (
                  STEPS.map((s) => (
                    <Badge key={s} tone={c.status === s ? (s === "APPROVED" ? "green" : "ink") : "default"}>
                      {s}
                    </Badge>
                  ))
                )}
              </div>
            </Row>
          );
        })
      )}
    </Panel>
  );
}
