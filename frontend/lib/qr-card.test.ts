import { afterEach, describe, expect, it, vi } from "vitest";
import { readQrToken, regenerateQrToken } from "./qr-card";

const originalFetch = globalThis.fetch;

afterEach(() => {
  globalThis.fetch = originalFetch;
  vi.restoreAllMocks();
});

function mockFetch(body: unknown) {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    text: async () => JSON.stringify(body),
  });
  globalThis.fetch = fetchMock as unknown as typeof fetch;
  return fetchMock;
}

describe("readQrToken", () => {
  it("reads the card without rotating it", async () => {
    const fetchMock = mockFetch({ token: "abc123" });
    const token = await readQrToken("jwt");

    expect(token).toBe("abc123");
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/records/emergency/qr");
    expect(init.method).toBe("GET");
    expect((init.headers as Record<string, string>).Authorization).toBe("Bearer jwt");
  });
});

describe("regenerateQrToken", () => {
  it("posts to rotate the token", async () => {
    const fetchMock = mockFetch({ token: "new456" });
    const token = await regenerateQrToken("jwt");

    expect(token).toBe("new456");
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/records/emergency/qr");
    expect(init.method).toBe("POST");
  });
});
