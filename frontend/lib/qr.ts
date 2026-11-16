/**
 * Helpers for reading the emergency QR code.
 *
 * The code printed on the patient's card carries the scanner address and the
 * signed token, for example:
 *
 *   https://example.org/scan?t=8fa10ccd3da9180b76a49bb3473f541c
 *
 * A responder may also receive the bare token, or a link that carries the
 * token under a different path. All of these are accepted.
 */

/** A signed emergency token is a hex string. */
const TOKEN = "[a-f0-9]{16,64}";

/**
 * Extract the signed token from a scanned QR payload.
 *
 * When the payload carries no recognisable token it is returned unchanged,
 * so the backend can reject it and report the problem instead of the scanner
 * silently doing nothing.
 */
export function tokenFromPayload(payload: string): string {
  const value = payload.trim();

  const query = new RegExp(`[?&]t=(${TOKEN})`, "i").exec(value);
  if (query) return query[1];

  const path = new RegExp(`/scan/(${TOKEN})`, "i").exec(value);
  if (path) return path[1];

  const bare = new RegExp(`^(${TOKEN})$`, "i").exec(value);
  if (bare) return bare[1];

  return value;
}

/**
 * The address encoded in the patient's QR code. It points at the public
 * scanner of whichever host the card is being shown on, so a phone that scans
 * it lands on the scanner page with the token filled in.
 */
export function scanAddress(origin: string, token: string): string {
  return `${origin.replace(/\/$/, "")}/scan?t=${token}`;
}
