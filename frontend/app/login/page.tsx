"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { TopNav } from "@/components/topnav";
import { apiFetch } from "@/lib/api";
import { useAuth, Session } from "@/lib/auth";
import { ErrorBanner } from "@/components/ui";

const DEMO = [
  { role: "patient", email: "aarav@abha.dev" },
  { role: "hospital", email: "city@abha.dev" },
  { role: "admin", email: "admin@abha.dev" },
];

export default function Login() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErr("");
    try {
      const s = await apiFetch<Session>("/api/identity/login", {
        method: "POST",
        body: { email, password },
      });
      login(s);
      router.push(s.role === "admin" ? "/admin" : s.role === "hospital" ? "/hospital" : "/patient");
    } catch (e2) {
      setErr((e2 as { detail: string }).detail);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <TopNav />
      <main className="max-w-md mx-auto px-6 py-16">
        <p className="label-caps mb-2">Access</p>
        <h1 className="font-display text-3xl font-semibold">Sign in</h1>
        <p className="text-sm text-stone mt-2">
          Patients, hospitals and administrators share one door. Your role decides what you see.
        </p>

        <ErrorBanner detail={err} />

        <form onSubmit={submit} className="mt-8 space-y-5">
          <div>
            <label className="field-label">Email</label>
            <input className="input" value={email} onChange={(e) => setEmail(e.target.value)} type="email" required placeholder="you@abha.dev" />
          </div>
          <div>
            <label className="field-label">Password</label>
            <input className="input" value={password} onChange={(e) => setPassword(e.target.value)} type="password" required placeholder="abha1234" />
          </div>
          <button className="btn w-full" disabled={busy}>
            {busy ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <div className="mt-10">
          <hr className="rule" />
          <p className="label-caps mt-4 mb-3">Demo credentials — password abha1234</p>
          <div className="space-y-2">
            {DEMO.map((d) => (
              <button
                key={d.email}
                onClick={() => {
                  setEmail(d.email);
                  setPassword("abha1234");
                }}
                className="w-full text-left px-3 py-2 border flex items-center justify-between cursor-pointer hover:bg-black/5"
                style={{ borderColor: "var(--line-soft)" }}
              >
                <span className="text-sm">{d.role}</span>
                <span className="mono text-xs text-stone">{d.email}</span>
              </button>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
