import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import jsQR from "jsqr";
import { EmergencyQr } from "./emergency-qr";
import { scanAddress } from "@/lib/qr";

const TOKEN = "8fa10ccd3da9180b76a49bb3473f541c";
const ORIGIN = "https://example.org";

type Matrix = { cells: number; dark: boolean[][] };

/**
 * Reads the module grid back out of the rendered SVG path so the test can
 * check the printed code the way a camera sees it.
 */
function readModules(svg: SVGSVGElement): Matrix {
  const viewBox = svg.getAttribute("viewBox") ?? "";
  const cells = Math.round(Number(viewBox.split(" ")[2]));
  const dark: boolean[][] = Array.from({ length: cells }, () => Array(cells).fill(false));

  const path = svg.querySelector('path[fill="#1c1917"]');
  const d = path?.getAttribute("d") ?? "";
  const run = /M(\d+)[ ,](\d+)\s*h(\d+)v1H\d+z/g;
  let match: RegExpExecArray | null;
  while ((match = run.exec(d)) !== null) {
    const x = Number(match[1]);
    const y = Number(match[2]);
    const width = Number(match[3]);
    for (let dx = 0; dx < width; dx += 1) {
      if (y >= 0 && y < cells && x + dx < cells) dark[y][x + dx] = true;
    }
  }
  return { cells, dark };
}

function rasterize(matrix: Matrix, scale = 8) {
  const width = matrix.cells * scale;
  const data = new Uint8ClampedArray(width * width * 4).fill(255);
  for (let y = 0; y < matrix.cells; y += 1) {
    for (let x = 0; x < matrix.cells; x += 1) {
      if (!matrix.dark[y][x]) continue;
      for (let py = 0; py < scale; py += 1) {
        for (let px = 0; px < scale; px += 1) {
          const offset = ((y * scale + py) * width + (x * scale + px)) * 4;
          data[offset] = 0;
          data[offset + 1] = 0;
          data[offset + 2] = 0;
          data[offset + 3] = 255;
        }
      }
    }
  }
  return { data, width, height: width };
}

describe("EmergencyQr", () => {
  it("keeps a four-module quiet zone around the code", () => {
    const { container } = render(<EmergencyQr origin={ORIGIN} token={TOKEN} />);
    const svg = container.querySelector("svg") as SVGSVGElement;
    const { cells, dark } = readModules(svg);

    let minX = cells;
    let maxX = -1;
    let minY = cells;
    let maxY = -1;
    for (let y = 0; y < cells; y += 1) {
      for (let x = 0; x < cells; x += 1) {
        if (!dark[y][x]) continue;
        minX = Math.min(minX, x);
        maxX = Math.max(maxX, x);
        minY = Math.min(minY, y);
        maxY = Math.max(maxY, y);
      }
    }

    expect(minX).toBeGreaterThanOrEqual(4);
    expect(minY).toBeGreaterThanOrEqual(4);
    expect(cells - 1 - maxX).toBeGreaterThanOrEqual(4);
    expect(cells - 1 - maxY).toBeGreaterThanOrEqual(4);
  });

  it("decodes back to the scan address", () => {
    const { container } = render(<EmergencyQr origin={ORIGIN} token={TOKEN} />);
    const svg = container.querySelector("svg") as SVGSVGElement;
    const image = rasterize(readModules(svg));

    const result = jsQR(image.data, image.width, image.height);
    expect(result?.data).toBe(scanAddress(ORIGIN, TOKEN));
  });

  it("encodes the address of the host the card is shown on", () => {
    const { container } = render(<EmergencyQr origin="http://localhost:3000" token={TOKEN} />);
    const svg = container.querySelector("svg") as SVGSVGElement;
    const image = rasterize(readModules(svg));

    const result = jsQR(image.data, image.width, image.height);
    expect(result?.data).toBe(`http://localhost:3000/scan?t=${TOKEN}`);
  });
});
