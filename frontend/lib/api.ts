export const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "";

export type ApiError = { status: number; detail: string };

export async function apiFetch<T>(
  path: string,
  opts: { method?: string; body?: unknown; token?: string | null } = {}
): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (opts.token) headers["Authorization"] = `Bearer ${opts.token}`;

  const res = await fetch(`${API_BASE}${path}`, {
    method: opts.method ?? "GET",
    headers,
    body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
  });

  const text = await res.text();
  let data: unknown = {};
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    data = {};
  }

  if (!res.ok) {
    const detail =
      (data as { detail?: string })?.detail ?? `Request failed (${res.status})`;
    throw { status: res.status, detail } as ApiError;
  }
  return data as T;
}

export const wsUrl =
  process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8005/ws";
