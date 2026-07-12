#!/usr/bin/env python3
"""
pixverse_nwm.py - Download PixVerse video WITHOUT watermark. NO LOGIN needed.

Works for PUBLIC videos: scrapes the <video> source from the public page
(the /ori/ URL is the clean no-WM file). Private videos require login.

Usage:
  python pixverse_nwm.py <video_id_or_url>

  Saves to ./downloads/<video_id>.mp4

Importable:
  from pixverse_nwm import download_video
  path = await download_video("413080782435081")
"""
import sys, os, re, argparse, asyncio, urllib.request
sys.path.insert(0, '/home/hermes/captcha-solver')
from playwright.async_api import async_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, "downloads")

def extract_vid(arg):
    m = re.search(r'(\d{10,})', arg)
    return m.group(1) if m else None

async def get_video_src(vid):
    """Open public page headless, return the clean /ori/ mp4 URL (no-WM)."""
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, args=["--no-sandbox","--disable-dev-shm-usage"])
        ctx = await b.new_context()
        pg = await ctx.new_page()
        src = [None]
        async def on_resp(resp):
            u = resp.url
            if "/ori/" in u and u.lower().endswith(".mp4"):
                src[0] = u
        pg.on("response", on_resp)
        await pg.goto(f"https://app.pixverse.ai/video/{vid}", wait_until="domcontentloaded", timeout=30000)
        await pg.wait_for_timeout(6000)
        # fallback: read <video> tags
        tags = await pg.evaluate("""()=>Array.from(document.querySelectorAll('video')).map(v=>v.src||v.currentSrc||'').filter(Boolean)""")
        await b.close()
        if src[0]:
            return src[0]
        for t in tags:
            if "/ori/" in t or t.endswith(".mp4"):
                return t
        return None

async def download_video(vid, account=None):
    """Download a public PixVerse video (no-WM) without login. Returns path."""
    vid = extract_vid(vid)
    if not vid:
        raise ValueError("cannot extract video_id")
    url = await get_video_src(vid)
    if not url:
        raise RuntimeError("no video url found (private or not ready)")
    os.makedirs(OUTDIR, exist_ok=True)
    fn = os.path.join(OUTDIR, f"{vid}.mp4")
    # curl carries Referer and works (urllib gets 403)
    import subprocess
    r = subprocess.run(["curl", "-s", "-L", "-e", "https://app.pixverse.ai/",
                        "-o", fn, url], capture_output=True)
    if r.returncode != 0 or os.path.getsize(fn) == 0:
        raise RuntimeError("download failed (curl rc=%d)" % r.returncode)
    return fn

async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="video_id or full URL")
    args = ap.parse_args()
    fn = await download_video(args.target)
    print("SAVED ->", fn)

if __name__ == "__main__":
    asyncio.run(main())
