"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import jsQR from "jsqr";
import { Camera, CameraOff } from "lucide-react";

type QrScannerProps = {
  /** Called with the raw payload once a code is read. */
  onDetected: (payload: string) => void;
};

type CameraState = "idle" | "starting" | "running" | "failed";

/**
 * Reads a QR code with the device camera.
 *
 * The camera is only started when the responder asks for it, and it is
 * released as soon as a code is read. A camera needs a secure origin, so this
 * works over HTTPS and on localhost, and reports the problem plainly when the
 * browser refuses.
 */
export function QrScanner({ onDetected }: QrScannerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const frameRef = useRef<number | null>(null);
  const [state, setState] = useState<CameraState>("idle");
  const [error, setError] = useState("");

  const release = useCallback(() => {
    if (frameRef.current !== null) {
      cancelAnimationFrame(frameRef.current);
      frameRef.current = null;
    }
    const stream = streamRef.current;
    if (stream) {
      for (const track of stream.getTracks()) track.stop();
      streamRef.current = null;
    }
    const video = videoRef.current;
    if (video) video.srcObject = null;
  }, []);

  const start = useCallback(async () => {
    setError("");
    setState("starting");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: "environment" } },
        audio: false,
      });
      streamRef.current = stream;

      const video = videoRef.current;
      const canvas = canvasRef.current;
      const context = canvas?.getContext("2d", { willReadFrequently: true });
      if (!video || !canvas || !context) {
        release();
        setState("failed");
        setError("This browser cannot read the camera image. Paste the token instead.");
        return;
      }

      video.srcObject = stream;
      video.setAttribute("playsinline", "true");
      await video.play();
      setState("running");

      const read = () => {
        const current = streamRef.current;
        if (!current) return;
        if (video.readyState === video.HAVE_ENOUGH_DATA) {
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          context.drawImage(video, 0, 0, canvas.width, canvas.height);
          const image = context.getImageData(0, 0, canvas.width, canvas.height);
          const code = jsQR(image.data, image.width, image.height, {
            inversionAttempts: "dontInvert",
          });
          if (code?.data) {
            release();
            setState("idle");
            onDetected(code.data);
            return;
          }
        }
        frameRef.current = requestAnimationFrame(read);
      };
      frameRef.current = requestAnimationFrame(read);
    } catch (e) {
      release();
      setState("failed");
      const name = (e as { name?: string })?.name;
      setError(
        name === "NotAllowedError"
          ? "Camera permission was refused. Allow it in the browser, or paste the token instead."
          : "No camera is available on this device. Paste the token instead."
      );
    }
  }, [onDetected, release]);

  const stop = useCallback(() => {
    release();
    setState("idle");
  }, [release]);

  useEffect(() => {
    return () => {
      release();
    };
  }, [release]);

  return (
    <div>
      <div className="flex items-center gap-3">
        <button
          type="button"
          className="btn btn-outline"
          onClick={() => (state === "running" ? stop() : start())}
          disabled={state === "starting"}
        >
          {state === "running" ? <CameraOff size={14} /> : <Camera size={14} />}
          {state === "running" ? "Stop camera" : state === "starting" ? "Starting camera" : "Scan with camera"}
        </button>
        {state === "running" && <span className="text-xs text-stone">Point the camera at the card.</span>}
      </div>

      {error && (
        <p className="text-xs mt-3" style={{ color: "var(--red)" }}>
          {error}
        </p>
      )}

      <div className={state === "running" ? "mt-4 border border-ink relative" : "hidden"}>
        <video ref={videoRef} muted playsInline className="w-full block" />
        <div className="absolute inset-0 pointer-events-none border-[14px] border-[rgba(245,242,234,0.35)]" />
      </div>
      <canvas ref={canvasRef} className="hidden" />
    </div>
  );
}
