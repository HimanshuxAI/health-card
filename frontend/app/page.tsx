"use client";

import Link from "next/link";
import { TopNav } from "@/components/topnav";
import { useAuth } from "@/lib/auth";
import { ArrowRight, ShieldCheck, QrCode, FileText, BellRing } from "lucide-react";

export default function Landing() {
  const { session } = useAuth();
  return (
    <div>
      <TopNav />
      <main className="max-w-6xl mx-auto px-6">
        {/* Hero */}
        <section className="pt-16 pb-10">
          <div className="grid grid-cols-1 md:grid-cols-[2fr_1fr] gap-10 items-start">
            <div>
              <p className="label-caps mb-4">Ayushman Bharat Digital Mission — Group SY1512</p>
              <h1 className="font-display text-5xl md:text-6xl leading-[1.05] font-semibold tracking-tight">
                Your health record,
                <br />
                readable in an
                <em style={{ color: "var(--green)" }}> emergency.</em>
              </h1>
              <p className="mt-6 max-w-xl text-stone leading-relaxed">
                A hybrid health card that works when the network does not. Scan the card,
                read the trauma profile in milliseconds, dispatch an SOS — then settle
                hospital bills through standardized FHIR claims on the NHCX.
              </p>
              <div className="mt-8 flex items-center gap-4 flex-wrap">
                {session ? (
                  <Link
                    href={session.role === "admin" ? "/admin" : session.role === "hospital" ? "/hospital" : "/patient"}
                    className="btn"
                  >
                    Open dashboard <ArrowRight size={14} />
                  </Link>
                ) : (
                  <>
                    <Link href="/login" className="btn">
                      Sign in <ArrowRight size={14} />
                    </Link>
                    <Link href="/scan" className="btn btn-outline">
                      Open emergency scanner
                    </Link>
                  </>
                )}
              </div>
            </div>

            {/* Editorial stat block */}
            <div className="border-l-2 border-ink pl-6 md:mt-2">
              <div className="label-caps mb-3">At a glance</div>
              <div className="space-y-5">
                <div>
                  <div className="stat-display">800<span className="text-2xl">ms</span></div>
                  <div className="text-xs text-stone mt-1">Emergency profile retrieval target</div>
                </div>
                <hr className="rule-soft" />
                <div>
                  <div className="stat-display">AES-128</div>
                  <div className="text-xs text-stone mt-1">GCM encryption on every trauma profile</div>
                </div>
                <hr className="rule-soft" />
                <div>
                  <div className="stat-display">FHIR v4</div>
                  <div className="text-xs text-stone mt-1">Records and claims, standardized</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <hr className="rule" />

        {/* Feature columns — editorial style */}
        <section className="py-12 grid grid-cols-1 md:grid-cols-4 gap-8">
          {[
            {
              icon: QrCode,
              title: "Emergency card",
              text: "A signed QR token resolves your blood group, allergies, chronic conditions and contacts — even when the patient cannot speak.",
            },
            {
              icon: ShieldCheck,
              title: "ABDM integration",
              text: "Tokenized eKYC, consent artifacts and care-context linking through simulated ABDM Sandbox v3 endpoints, fully audited.",
            },
            {
              icon: FileText,
              title: "FHIR records",
              text: "Prescriptions, diagnostics and immunizations converted into HL7 FHIR v4 resources at write time. No retro-mapping.",
            },
            {
              icon: BellRing,
              title: "Live SOS dispatch",
              text: "Panic button or scan-triggered alerts hit hospital dashboards in real time and email every registered emergency contact.",
            },
          ].map((f) => (
            <div key={f.title} className="border-t-2 border-ink pt-4">
              <f.icon size={18} strokeWidth={2} />
              <h3 className="font-display text-lg font-semibold mt-3">{f.title}</h3>
              <p className="text-sm text-stone mt-2 leading-relaxed">{f.text}</p>
            </div>
          ))}
        </section>

        <hr className="rule" />

        <footer className="py-6 flex items-center justify-between">
          <span className="label-caps">ABHA Health Card — MIT-ADT University, 2026</span>
          <span className="label-caps">ABDM Sandbox simulated offline</span>
        </footer>
      </main>
    </div>
  );
}
