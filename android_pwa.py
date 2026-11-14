import struct
import zlib
from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response

pwa_router = APIRouter()

LOGO_SVG = """<svg xmlns="http://w3.org" viewBox="0 0 120 120" width="52" height="52">
  <defs>
    <linearGradient id="smGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#4F46E5"/>
      <stop offset="100%" stop-color="#312E81"/>
    </linearGradient>
  </defs>
  <path d="M60 8 L104 24 V58 C104 86 84 105 60 113 C36 105 16 86 16 58 V24 Z" fill="url(#smGrad)" stroke="#F59E0B" stroke-width="5"/>
  <path d="M74 42 H50 C44 42 40 46 40 51 C40 56 44 60 50 60 H70 C76 60 80 64 80 69 C80 74 76 78 70 78 H46" fill="none" stroke="#F59E0B" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>
</svg>"""

def build_securemonie_png(size: int) -> bytes:
    rows = []
    pad = int(size * 0.14)
    stroke = max(4, int(size * 0.10))
    mid = size // 2
    s_pad = int(size * 0.27)
    for y in range(size):
        row = bytearray([0])
        for x in range(size):
            dx = abs(x - mid)
            in_shield = (y >= pad) and (y <= size - pad) and (dx <= (mid - pad) * (1.0 - max(0, y - mid) / (size * 1.15)))
            is_border = in_shield and (
                y < pad + max(3, size // 32)
                or dx > (mid - pad) * (1.0 - max(0, y - mid) / (size * 1.15)) - max(3, size // 28)
            )
            in_s_box = s_pad <= x <= size - s_pad and s_pad <= y <= size - s_pad
            is_s = False
            if in_s_box:
                top_bar = y < s_pad + stroke
                mid_bar = abs(y - mid) <= stroke // 2
                bot_bar = y > size - s_pad - stroke
                left_leg = (s_pad <= y <= mid) and (x < s_pad + stroke)
                right_leg = (mid <= y <= size - s_pad) and (x > size - s_pad - stroke)
                is_s = top_bar or mid_bar or bot_bar or left_leg or right_leg

            if is_s or is_border:
                row.extend([245, 158, 11, 255])  # Sovereign Gold (#F59E0B)
            elif in_shield:
                row.extend([79, 70, 229, 255])   # Royal Indigo (#4F46E5)
            else:
                row.extend([11, 16, 33, 255])    # Deep Midnight (#0B1021)
        rows.append(bytes(row))
    raw_data = zlib.compress(b"".join(rows))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack("!I", len(data)) + tag + data + struct.pack("!I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack("!IIBBBBB", size, size, 8, 6, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", raw_data) + chunk(b"IEND", b"")

ICON_192 = build_securemonie_png(192)
ICON_512 = build_securemonie_png(512)

SW_JS = """
const CACHE_NAME = "securemonie-v2";
self.addEventListener("install", (e) => {
    e.waitUntil(caches.open(CACHE_NAME).then((c) => c.addAll(["/", "/manifest.json", "/icon-192.png"])));
    self.skipWaiting();
});
self.addEventListener("activate", (e) => {
    e.waitUntil(self.clients.claim());
});
self.addEventListener("fetch", (e) => {
    if (e.request.method !== "GET") return;
    e.respondWith(fetch(e.request).catch(() => caches.match(e.request)));
});
"""

@pwa_router.get("/manifest.json")
def android_manifest():
    return JSONResponse({
        "id": "/?app=securemonie-v2",
        "name": "Securemonie Microfinance Bank",
        "short_name": "Securemonie",
        "description": "Personal & Business Microfinance Banking, Instant Transfers & Target Savings",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "orientation": "portrait",
        "background_color": "#0b1021",
        "theme_color": "#4f46e5",
        "icons": [
            {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
        ],
    })

@pwa_router.get("/icon-192.png")
def icon_192():
    return Response(content=ICON_192, media_type="image/png")

@pwa_router.get("/icon-512.png")
def icon_512():
    return Response(content=ICON_512, media_type="image/png")

@pwa_router.get("/sw.js")
def service_worker():
    return Response(content=SW_JS, media_type="application/javascript")
