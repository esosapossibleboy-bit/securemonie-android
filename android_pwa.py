import struct
import zlib
from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response

pwa_router = APIRouter()

def build_securemonie_png(size: int) -> bytes:
    rows = []
    pad = int(size * 0.18)
    stroke = max(4, int(size * 0.11))
    mid = size // 2
    for y in range(size):
        row = bytearray([0])
        for x in range(size):
            in_box = pad <= x <= size - pad and pad <= y <= size - pad
            is_s = False
            if in_box:
                top_bar = y < pad + stroke
                mid_bar = abs(y - mid) <= stroke // 2
                bot_bar = y > size - pad - stroke
                left_leg = (pad <= y <= mid) and (x < pad + stroke)
                right_leg = (mid <= y <= size - pad) and (x > size - pad - stroke)
                is_s = top_bar or mid_bar or bot_bar or left_leg or right_leg
            if is_s:
                row.extend([255, 255, 255, 255])
            else:
                row.extend([0, 184, 117, 255])
        rows.append(bytes(row))
    raw_data = zlib.compress(b"".join(rows))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack("!I", len(data)) + tag + data + struct.pack("!I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack("!IIBBBBB", size, size, 8, 6, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", raw_data) + chunk(b"IEND", b"")

ICON_192 = build_securemonie_png(192)
ICON_512 = build_securemonie_png(512)

SW_JS = """
const CACHE_NAME = "securemonie-v1";
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
        "id": "/?app=securemonie",
        "name": "Securemonie Microfinance Bank",
        "short_name": "Securemonie",
        "description": "Fast, secure mobile microfinance wallet, savings, and instant transfers",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "orientation": "portrait",
        "background_color": "#090f18",
        "theme_color": "#00b875",
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
