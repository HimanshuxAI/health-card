"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";

export type Session = {
  access_token: string;
  role: "patient" | "hospital" | "admin";
  abha_id: string | null;
  name: string;
  user_id: number;
};

type AuthCtx = {
  session: Session | null;
  ready: boolean;
  login: (s: Session) => void;
  logout: () => void;
};

const Ctx = createContext<AuthCtx>({
  session: null,
  ready: false,
  login: () => {},
  logout: () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    try {
      const raw = localStorage.getItem("abha_session");
      if (raw) setSession(JSON.parse(raw));
    } catch {}
    setReady(true);
  }, []);

  const login = useCallback((s: Session) => {
    localStorage.setItem("abha_session", JSON.stringify(s));
    setSession(s);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("abha_session");
    setSession(null);
  }, []);

  return (
    <Ctx.Provider value={{ session, ready, login, logout }}>
      {children}
    </Ctx.Provider>
  );
}

export function useAuth() {
  return useContext(Ctx);
}
