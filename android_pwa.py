import os
import struct
import zlib
from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response

pwa_router = APIRouter()

LOGO_SVG = """
<svg width="36" height="36" viewBox="0 0 64 64" fill="none" xmlns="http://w3.org">
  <defs>
    <linearGradient id="smGrad" x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#f59e0b"/>
      <stop offset="100%" stop-color="#4f46e5"/>
    </linearGradient>
  </defs>
  <rect width="64" height="64" rx="16" fill="url(#smGrad)"/>
  <path d="M32 12L48 19V31C48 41.5 41.2 50.8 32 54C22.8 50.8 16 41.5 16 31V19L32 12Z" fill="#0b1021" stroke="#fbbf24" stroke-width="2.5"/>
  <path d="M25 32.5L30 37.5L40 26.5" stroke="#34d399" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""

def _make_png(size: int) -> bytes:
    raw = bytearray()
    for y in range(size):
        raw.append(0)
        for x in range(size):
            border = x < size * 0.08 or x > size * 0.92 or y < size * 0.08 or y > size * 0.92
            r, g, b = (245, 158, 11) if border else (15, 23, 42)
            raw.extend((r, g, b, 255))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(bytes(raw))) + chunk(b"IEND", b"")

@pwa_router.get("/icon-192.png")
def icon_192():
    return Response(content=_make_png(192), media_type="image/png")

@pwa_router.get("/icon-512.png")
def icon_512():
    return Response(content=_make_png(512), media_type="image/png")

@pwa_router.get("/manifest.json")
def manifest():
    return JSONResponse({
        "name": "Securemonie Microfinance Bank",
        "short_name": "Securemonie",
        "description": "Smart Mobile Banking, Transfers, Virtual Cards & High-Yield Savings",
        "start_url": "/",
        "display": "standalone",
        "orientation": "portrait",
        "background_color": "#0b1021",
        "theme_color": "#4f46e5",
        "icons": [
            {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
            {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
        ],
    })

@pwa_router.get("/.well-known/assetlinks.json")
def assetlinks():
    pkg = os.getenv("ANDROID_PACKAGE_NAME", "com.securemonie.mfb.twa")
    sha256 = os.getenv("ANDROID_SHA256_FINGERPRINT", "")
    if not sha256:
        return JSONResponse([])
    return JSONResponse([{
        "relation": ["delegate_permission/common.handle_all_urls"],
        "target": {
            "namespace": "android_app",
            "package_name": pkg,
            "sha256_cert_fingerprints": [sha256],
        },
    }])

@pwa_router.get("/sw.js")
def service_worker():
    code = """
    const CACHE = "securemonie-v4";
    self.addEventListener("install", e => { self.skipWaiting(); });
    self.addEventListener("activate", e => { e.waitUntil(clients.claim()); });
    self.addEventListener("fetch", e => {
        if (e.request.method !== "GET" || e.request.url.includes("/api/")) return;
        e.respondWith(fetch(e.request).catch(() => caches.match(e.request)));
    });
    """
    return Response(content=code, media_type="application/javascript")
