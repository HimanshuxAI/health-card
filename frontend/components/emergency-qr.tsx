"use client";

import { QRCodeSVG } from "qrcode.react";
import { scanAddress } from "@/lib/qr";

type EmergencyQrProps = {
  /** The address the card is being shown at. */
  origin: string;
  /** The signed emergency token. */
  token: string;
  size?: number;
};

/**
 * The emergency QR printed on the patient's card.
 *
 * The settings here are the difference between a code that a phone can read
 * and one that it cannot:
 *
 * - `marginSize={4}` adds the four-module quiet zone the QR specification
 *   requires. Without it the code sits flush against the panel edge and most
 *   camera decoders refuse it.
 * - `level="H"` keeps 30 percent of the code recoverable, which covers a
 *   printed card that is creased, scratched or lit poorly.
 * - `shapeRendering="crispEdges"` stops the browser smoothing the module
 *   edges into grey gradients, which blurs the finder patterns.
 */
export function EmergencyQr({ origin, token, size = 220 }: EmergencyQrProps) {
  return (
    <QRCodeSVG
      value={scanAddress(origin, token)}
      size={size}
      level="H"
      marginSize={4}
      bgColor="#ffffff"
      fgColor="#1c1917"
      title="Emergency health card"
      style={{ shapeRendering: "crispEdges" }}
    />
  );
}
