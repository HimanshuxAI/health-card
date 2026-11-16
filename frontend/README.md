# Frontend

Next.js 16 App Router frontend for the ABHA Health Card project: the patient area, the hospital
workspace, the administrator console and the public emergency scanner.

## Run against the services

The frontend talks to the API through `/api/*`. `next.config.ts` rewrites those paths to the
service that owns them.

- In Docker, set `API_GATEWAY_URL` to the gateway address (`http://gateway:80`) at build time.
  Next writes rewrite destinations into the production bundle, so it has to be present during the
  build.
- Locally, each service is reached on its own port: identity 8001, records 8002, abdm 8003,
  nhcx 8004, sos 8005.

## Commands

```bash
npm install
npm run dev        # development server on http://localhost:3000
npm test           # vitest, single run
npx next typegen   # generate route types (needed before a standalone type check)
npx tsc --noEmit   # type check
npm run build      # production build
```

## The emergency QR

The code on the patient's card is printed by `components/emergency-qr.tsx`. Three settings decide
whether a phone can read it, and they are covered by `components/emergency-qr.test.tsx`:

- `marginSize={4}` adds the four-module quiet zone. Without it the code sits flush against the
  panel edge and most camera decoders refuse it.
- `level="H"` keeps 30 percent of the code recoverable, which covers a creased or badly lit card.
- `shapeRendering="crispEdges"` stops the browser smoothing module edges into grey gradients.

`components/qr-scanner.tsx` reads a code with the camera through `getUserMedia` and decodes it
with `jsQR`. It is used on the public scanner page and on the hospital scan desk. A camera needs
a secure origin, so it works over HTTPS and on `localhost` and not over plain HTTP on a LAN
address; the token can always be pasted instead.

## Notes

- The WebSocket address for the live SOS feed is derived from the current origin at runtime, so
  the feed reaches the gateway on whatever host and scheme the app is served from. Set
  `NEXT_PUBLIC_WS_URL` to override it.
- The visual language is editorial: warm paper, ink and hairlines, a serif display face, and
  red reserved for emergency states.
