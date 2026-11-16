import { describe, expect, it } from "vitest";
import { scanAddress, tokenFromPayload } from "./qr";

describe("tokenFromPayload", () => {
  it("extracts token from a standard scan URL", () => {
    const payload = "https://example.org/scan?t=8fa10ccd3da9180b76a49bb3473f541c";
    expect(tokenFromPayload(payload)).toBe("8fa10ccd3da9180b76a49bb3473f541c");
  });

  it("extracts token when additional query parameters exist", () => {
    const payload = "https://example.org/scan?src=cam&t=8fa10ccd3da9180b76a49bb3473f541c&v=1";
    expect(tokenFromPayload(payload)).toBe("8fa10ccd3da9180b76a49bb3473f541c");
  });

  it("accepts a bare hex token", () => {
    const token = "8fa10ccd3da9180b76a49bb3473f541c";
    expect(tokenFromPayload(token)).toBe(token);
  });

  it("trims whitespace around the input", () => {
    const token = " 8fa10ccd3da9180b76a49bb3473f541c \n";
    expect(tokenFromPayload(token)).toBe("8fa10ccd3da9180b76a49bb3473f541c");
  });

  it("extracts token from a path-based scan URL", () => {
    const payload = "https://example.org/scan/8fa10ccd3da9180b76a49bb3473f541c";
    expect(tokenFromPayload(payload)).toBe("8fa10ccd3da9180b76a49bb3473f541c");
  });

  it("returns invalid input as-is so the backend can report a formal error", () => {
    expect(tokenFromPayload("invalid-token-format")).toBe("invalid-token-format");
  });
});

describe("scanAddress", () => {
  it("constructs the full target URL without duplicate slashes", () => {
    expect(scanAddress("https://example.org/", "abc1234567890def")).toBe(
      "https://example.org/scan?t=abc1234567890def"
    );
    expect(scanAddress("https://example.org", "abc1234567890def")).toBe(
      "https://example.org/scan?t=abc1234567890def"
    );
  });
});
