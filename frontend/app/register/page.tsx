"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { TopNav } from "@/components/topnav";
import { apiFetch } from "@/lib/api";
import { useAuth, Session } from "@/lib/auth";
import { ErrorBanner } from "@/components/ui";

export default function Register() {
  const router = useRouter();
  const { login } = useAuth();
  const [role, setRole] = useState<"patient" | "hospital">("patient");
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    abha_id: "",
    phone: "",
    hospital_name: "",
  });
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  function set(k: string, v: string) {
    setForm((f) => ({ ...f, [k]: v }));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErr("");
    try {
      const body =
        role === "hospital"
          ? { name: form.name, email: form.email, password: form.password, role, hospital_name: form.hospital_name }
          : {
              name: form.name,
              email: form.email,
              password: form.password,
              role,
              abha_id: form.abha_id || undefined,
              phone: form.phone || undefined,
            };
      const s = await apiFetch<Session>("/api/identity/register", {
        method: "POST",
        body,
      });
      login(s);
      router.push(role === "hospital" ? "/hospital" : "/patient");
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
        <h1 className="font-display text-3xl font-semibold">Create an account</h1>

        <ErrorBanner detail={err} />

        <div className="mt-6 flex gap-0 border border-ink">
          {(["patient", "hospital"] as const).map((r) => (
            <button
              key={r}
              onClick={() => setRole(r)}
              className="flex-1 py-2.5 text-xs font-semibold uppercase tracking-widest cursor-pointer"
              style={role === r ? { background: "var(--ink)", color: "var(--paper)" } : undefined}
            >
              {r}
            </button>
          ))}
        </div>

        <form onSubmit={submit} className="mt-8 space-y-5">
          <div>
            <label className="field-label">Full name</label>
            <input className="input" value={form.name} onChange={(e) => set("name", e.target.value)} required />
          </div>
          <div>
            <label className="field-label">Email</label>
            <input className="input" type="email" value={form.email} onChange={(e) => set("email", e.target.value)} required />
          </div>
          <div>
            <label className="field-label">Password</label>
            <input className="input" type="password" value={form.password} onChange={(e) => set("password", e.target.value)} required minLength={6} />
          </div>
          {role === "patient" ? (
            <>
              <div>
                <label className="field-label">ABHA ID (14 digits — optional, can link later)</label>
                <input className="input mono" value={form.abha_id} onChange={(e) => set("abha_id", e.target.value.replace(/\D/g, "").slice(0, 14))} placeholder="12345678901234" />
              </div>
              <div>
                <label className="field-label">Phone</label>
                <input className="input" value={form.phone} onChange={(e) => set("phone", e.target.value)} placeholder="+91-90000-00000" />
              </div>
            </>
          ) : (
            <div>
              <label className="field-label">Hospital name</label>
              <input className="input" value={form.hospital_name} onChange={(e) => set("hospital_name", e.target.value)} required />
            </div>
          )}
          <button className="btn w-full" disabled={busy}>
            {busy ? "Creating..." : `Register as ${role}`}
          </button>
        </form>
      </main>
    </div>
  );
}
