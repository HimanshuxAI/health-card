import { apiFetch } from "./api";

/**
 * The emergency card token.
 *
 * Reading the card is a GET and never rotates the token, so a copy that is
 * already printed keeps working. Rotating is a deliberate act: the patient
 * presses "Regenerate card", the previous copy stops working, and a new one
 * is issued.
 */
export async function readQrToken(accessToken?: string | null): Promise<string> {
  const r = await apiFetch<{ token: string }>("/api/records/emergency/qr", { token: accessToken });
  return r.token;
}

/** Issue a new card and invalidate the old one. */
export async function regenerateQrToken(accessToken?: string | null): Promise<string> {
  const r = await apiFetch<{ token: string }>("/api/records/emergency/qr", {
    method: "POST",
    token: accessToken,
  });
  return r.token;
}
