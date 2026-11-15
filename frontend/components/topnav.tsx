"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { ActivitySquare } from "lucide-react";

export function TopNav() {
  const { session, logout } = useAuth();
  const home = session
    ? session.role === "admin"
      ? "/admin"
      : session.role === "hospital"
        ? "/hospital"
        : "/patient"
    : "/";

  return (
    <header className="border-b border-ink">
      <div className="max-w-6xl mx-auto px-6 py-3 flex items-center gap-6">
        <Link href={home} className="flex items-center gap-2">
          <ActivitySquare size={18} strokeWidth={2.2} />
          <span className="font-display text-lg font-semibold tracking-tight">
            ABHA<span style={{ color: "var(--green)" }}>.</span>Card
          </span>
        </Link>
        <span className="label-caps hidden sm:inline">Digital Health Mission</span>
        <nav className="ml-auto flex items-center gap-5 text-xs">
          {!session && (
            <>
              <Link href="/scan" className="hover:underline underline-offset-4">
                Emergency Scanner
              </Link>
              <Link href="/login" className="hover:underline underline-offset-4">
                Sign in
              </Link>
              <Link href="/register" className="badge badge-ink">
                Register
              </Link>
            </>
          )}
          {session && (
            <>
              <span className="label-caps hidden sm:inline">{session.name}</span>
              <span className="badge">{session.role}</span>
              <Link href={home} className="hover:underline underline-offset-4">
                Dashboard
              </Link>
              <button
                onClick={logout}
                className="hover:underline underline-offset-4 cursor-pointer"
              >
                Sign out
              </button>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
