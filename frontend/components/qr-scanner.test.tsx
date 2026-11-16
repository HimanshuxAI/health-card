import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import jsQR from "jsqr";
import { QrScanner } from "./qr-scanner";

vi.mock("jsqr", () => ({ default: vi.fn() }));

const mockedJsQr = vi.mocked(jsQR);

type FakeTrack = { stop: ReturnType<typeof vi.fn> };

function fakeStream(): { stream: MediaStream; tracks: FakeTrack[] } {
  const tracks: FakeTrack[] = [{ stop: vi.fn() }, { stop: vi.fn() }];
  const stream = {
    getTracks: () => tracks,
  } as unknown as MediaStream;
  return { stream, tracks };
}

function mockCamera(stream: MediaStream) {
  Object.defineProperty(navigator, "mediaDevices", {
    configurable: true,
    value: { getUserMedia: vi.fn().mockResolvedValue(stream) },
  });
}

function mockVideoFrame() {
  Object.defineProperty(HTMLMediaElement.prototype, "play", {
    configurable: true,
    value: vi.fn().mockResolvedValue(undefined),
  });
  const width = 640;
  const height = 480;
  HTMLCanvasElement.prototype.getContext = vi.fn().mockReturnValue({
    drawImage: vi.fn(),
    getImageData: vi.fn().mockReturnValue({
      data: new Uint8ClampedArray(width * height * 4),
      width,
      height,
    }),
  }) as unknown as HTMLCanvasElement["getContext"];
  // jsdom keeps media elements at readyState 0 and reports a zero-sized frame.
  Object.defineProperty(HTMLVideoElement.prototype, "readyState", {
    configurable: true,
    get: () => 4,
  });
  Object.defineProperty(HTMLVideoElement.prototype, "videoWidth", {
    configurable: true,
    get: () => width,
  });
  Object.defineProperty(HTMLVideoElement.prototype, "videoHeight", {
    configurable: true,
    get: () => height,
  });
}

describe("QrScanner", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockVideoFrame();
  });

  it("reports the payload once a code is decoded", async () => {
    const { stream, tracks } = fakeStream();
    mockCamera(stream);
    mockedJsQr.mockReturnValue({ data: "https://example.org/scan?t=abc123" } as never);

    const onDetected = vi.fn();
    render(<QrScanner onDetected={onDetected} />);

    fireEvent.click(screen.getByRole("button", { name: /scan with camera/i }));

    await waitFor(() => expect(onDetected).toHaveBeenCalledWith("https://example.org/scan?t=abc123"));
    expect(tracks.every((t) => t.stop.mock.calls.length === 1)).toBe(true);
  });

  it("keeps reading frames until a code is found", async () => {
    const { stream } = fakeStream();
    mockCamera(stream);
    mockedJsQr.mockReturnValueOnce(null as never).mockReturnValueOnce({ data: "token-abc" } as never);

    const onDetected = vi.fn();
    render(<QrScanner onDetected={onDetected} />);

    fireEvent.click(screen.getByRole("button", { name: /scan with camera/i }));

    await waitFor(() => expect(onDetected).toHaveBeenCalledWith("token-abc"));
    expect(mockedJsQr.mock.calls.length).toBeGreaterThanOrEqual(2);
  });

  it("keeps reading frames when the browser stops handing out animation frames", async () => {
    // A browser stops calling requestAnimationFrame when its window is not
    // focused. The scan must not depend on it.
    const raf = vi.spyOn(window, "requestAnimationFrame").mockImplementation(() => 0);
    const { stream } = fakeStream();
    mockCamera(stream);
    mockedJsQr.mockReturnValue({ data: "token-unfocused" } as never);

    const onDetected = vi.fn();
    render(<QrScanner onDetected={onDetected} />);

    fireEvent.click(screen.getByRole("button", { name: /scan with camera/i }));

    await waitFor(() => expect(onDetected).toHaveBeenCalledWith("token-unfocused"));
    raf.mockRestore();
  });

  it("explains a refused camera permission and offers the manual fallback", async () => {
    Object.defineProperty(navigator, "mediaDevices", {
      configurable: true,
      value: {
        getUserMedia: vi.fn().mockRejectedValue(Object.assign(new Error("denied"), { name: "NotAllowedError" })),
      },
    });

    render(<QrScanner onDetected={vi.fn()} />);
    fireEvent.click(screen.getByRole("button", { name: /scan with camera/i }));

    await waitFor(() => expect(screen.getByText(/camera permission was refused/i)).toBeTruthy());
  });

  it("reports a missing camera", async () => {
    Object.defineProperty(navigator, "mediaDevices", {
      configurable: true,
      value: {
        getUserMedia: vi.fn().mockRejectedValue(Object.assign(new Error("none"), { name: "NotFoundError" })),
      },
    });

    render(<QrScanner onDetected={vi.fn()} />);
    fireEvent.click(screen.getByRole("button", { name: /scan with camera/i }));

    await waitFor(() => expect(screen.getByText(/no camera is available/i)).toBeTruthy());
  });
});
