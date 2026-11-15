"use client";

import { Suspense, useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { AlertTriangle, PhoneCall } from "lucide-react";
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
  emergency_contacts: { name: string; phone: string; relation: string }[];
};

function Scanner() {
  const { session } = useAuth();
  const params = useSearchParams();
  const [token, setToken] = useState("");
  const [phase, setPhase] = useState<"idle" | "resolving" | "done">("idle");
  const [lines, setLines] = useState<string[]>([]);
  const [resolved, setResolved] = useState<{ profile: Profile; retrieved_in_ms: number } | null>(null);
  const [err, setErr] = useState("");
  const [sosSent, setSosSent] = useState(false);
  const geoRef = useRef<{ lat: number | null; lng: number | null }>({ lat: null, lng: null });
  const startedRef = useRef<string | null>(null);

  useEffect(() => {
    const t = params.get("t");
    if (t) {
      setToken(t);
    }
    navigator.geolocation?.getCurrentPosition(
      (pos) => (geoRef.current = { lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => {},
      { timeout: 5000 }
    );
  }, [params]);

  const resolve = useCallback(async (tok: string) => {
    if (!tok.trim()) return;
    if (startedRef.current === tok.trim()) return; // guard against double-run
    startedRef.current = tok.trim();
    setErr("");
    setPhase("resolving");
    setLines([]);
    setResolved(null);
    try {
      const r = await apiFetch<{ profile: Profile; retrieved_in_ms: number }>(`/api/records/emergency/resolve/${tok.trim()}`);
      const p = r.profile;
      const reveal = [
        `name:        ${p.full_name || "—"}`,
        `abha:        ${p.abha_id ?? "—"}`,
        `blood:       ${p.blood_group || "—"}`,
        `allergies:   ${p.allergies.join(", ") || "none recorded"}`,
        `conditions:  ${p.chronic_conditions.join(", ") || "none recorded"}`,
        `medications: ${p.medications.join(", ") || "none recorded"}`,
        `contacts:    ${p.emergency_contacts.map((c) => `${c.name} (${c.phone})`).join("; ") || "none recorded"}`,
      ];
      reveal.forEach((line, i) => setTimeout(() => setLines((prev) => [...prev, line]), 200 * (i + 1)));
      setTimeout(() => {
        setResolved(r);
        setPhase("done");
      }, 200 * (reveal.length + 1));
    } catch (e) {
      setErr((e as { detail: string }).detail);
      setPhase("idle");
    }
  }, []);

  // auto-resolve when arriving from a QR link
  useEffect(() => {
    const t = params.get("t");
    if (t && phase === "idle") resolve(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params]);

  async function dispatchSos() {
    setErr("");
    try {
      await apiFetch("/api/sos/alerts", {
        method: "POST",
        token: session?.access_token,
        body: {
          patient_id: 0,
          trigger: "QR_SCAN",
          lat: geoRef.current.lat,
          lng: geoRef.current.lng,
          location_label: "Emergency scene (public scanner)",
        },
      });
      setSosSent(true);
    } catch (e) {
      // public scanner may be unauthenticated; the alert endpoint requires auth for
      // dispatch — surface it clearly
      setErr((e as { detail: string }).detail);
    }
  }

  return (
    <div>
      <TopNav />
      <main className="max-w-3xl mx-auto px-6 py-10">
        <div className="flex items-center justify-between">
          <div>
            <p className="label-caps" style={{ color: "var(--red)" }}>Public emergency access — no login required</p>
            <h1 className="font-display text-3xl font-semibold mt-1">Emergency Scanner</h1>
          </div>
          <Badge tone="red">Critical care protocol</Badge>
        </div>

        <ErrorBanner detail={err} />

        <div className="mt-6 flex gap-2">
          <input
            className="input mono"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="Enter the token printed under the patient's QR"
            onKeyDown={(e) => e.key === "Enter" && resolve(token)}
          />
          <button className="btn shrink-0" onClick={() => resolve(token)} disabled={phase === "resolving"}>
            {phase === "resolving" ? "Decrypting" : "Resolve"}
          </button>
        </div>

        <div className="mt-6 grid md:grid-cols-2 gap-6">
          <Panel title="Trauma profile" right={resolved ? <Badge tone="green">{resolved.retrieved_in_ms < 1 ? "<1" : resolved.retrieved_in_ms}ms</Badge> : undefined}>
            {phase === "idle" && <EmptyState text="Awaiting token. Scanning a QR lands here pre-filled." />}
            {phase !== "idle" && (
              <pre className="mono text-xs leading-6 whitespace-pre-wrap">
                {lines.map((l) => l + "\n")}
                {phase === "resolving" && <span className="animate-pulse">▮</span>}
              </pre>
            )}
          </Panel>

          <div className="space-y-4">
            <Panel title="Dispatch emergency SOS">
              <p className="text-xs text-stone mb-4">
                Fires a live alert to every hospital dashboard and emails the patient's registered
                emergency contacts with your GPS position.
              </p>
              {sosSent ? (
                <Badge tone="green">SOS dispatched — responders notified</Badge>
              ) : (
                <button className="btn btn-danger" onClick={dispatchSos} disabled={phase !== "done"}>
                  Dispatch SOS now
                </button>
              )}
            </Panel>

            {resolved && resolved.profile.emergency_contacts.length > 0 && (
              <Panel title="Call emergency contacts directly" flush>
                {resolved.profile.emergency_contacts.map((c, i) => (
                  <Row key={i}>
                    <PhoneCall size={14} />
                    <span className="text-sm font-medium">{c.name}</span>
                    <span className="text-xs text-stone">{c.relation}</span>
                    <a href={`tel:${c.phone}`} className="btn btn-outline ml-auto shrink-0">{c.phone}</a>
                  </Row>
                ))}
              </Panel>
            )}

            {resolved && resolved.profile.allergies.length > 0 && (
              <div className="border px-4 py-3 flex items-center gap-3" style={{ borderColor: "var(--red)", background: "var(--red-soft)" }}>
                <AlertTriangle size={16} style={{ color: "var(--red)" }} />
                <div className="text-xs" style={{ color: "var(--red)" }}>
                  <strong>Severe allergies:</strong> {resolved.profile.allergies.join(", ")} — check before administering any drug.
                </div>
              </div>
            )}
          </div>
        </div>

        <p className="text-xs text-stone mt-10">
          This scanner works without a patient account.{" "}
          <Link href="/login" className="underline underline-offset-4">Responders with accounts</Link> get the full workflow.
        </p>
      </main>
    </div>
  );
}

export default function ScanPage() {
  return (
    <Suspense fallback={null}>
      <Scanner />
    </Suspense>
  );
}
