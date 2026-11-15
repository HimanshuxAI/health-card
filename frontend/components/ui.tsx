"use client";

import { ReactNode } from "react";

export function Stat({
  label,
  value,
  accent,
}: {
  label: string;
  value: ReactNode;
  accent?: "red" | "green";
}) {
  return (
    <div className="pt-3" style={{ borderTop: `3px solid ${accent === "red" ? "var(--red)" : accent === "green" ? "var(--green)" : "var(--stone-light)"}` }}>
      <div className="label-caps">{label}</div>
      <div className="stat-display-sm mt-1" style={accent ? { color: accent === "red" ? "var(--red)" : "var(--green)" } : undefined}>
        {value}
      </div>
    </div>
  );
}

export function Panel({
  title,
  right,
  children,
  flush,
}: {
  title: string;
  right?: ReactNode;
  children: ReactNode;
  flush?: boolean;
}) {
  return (
    <section className="panel">
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-ink">
        <h3 className="label-caps" style={{ color: "var(--ink)" }}>{title}</h3>
        {right}
      </div>
      <div className={flush ? "" : "p-4"}>{children}</div>
    </section>
  );
}

export function Badge({
  children,
  tone = "default",
}: {
  children: ReactNode;
  tone?: "default" | "green" | "red" | "ink";
}) {
  const cls = tone === "green" ? "badge badge-green" : tone === "red" ? "badge badge-red" : tone === "ink" ? "badge badge-ink" : "badge";
  return <span className={cls}>{children}</span>;
}

export function EmptyState({ text }: { text: string }) {
  return (
    <div className="py-10 text-center">
      <p className="font-display text-stone italic">{text}</p>
    </div>
  );
}

export function ErrorBanner({ detail }: { detail: string }) {
  if (!detail) return null;
  return (
    <div className="border px-4 py-2.5 my-3 text-sm" style={{ borderColor: "var(--red)", background: "var(--red-soft)", color: "var(--red)" }}>
      {detail}
    </div>
  );
}

export function Row({ children }: { children: ReactNode }) {
  return (
    <div className="px-4 py-3 flex items-center gap-4 border-b last:border-b-0" style={{ borderColor: "var(--line-soft)" }}>
      {children}
    </div>
  );
}
