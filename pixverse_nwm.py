#!/usr/bin/env python3
"""
pixverse_nwm.py - Download PixVerse video WITHOUT watermark via API.

Usage:
  python pixverse_nwm.py <video_id_or_url> [--account pixhok9yc@helixa.web.id]

- Resolves video_id from URL (https://app.pixverse.ai/video/XXXXXXXX)
- Logs in via an account from pixverse_accounts.txt (any account works to read
  public video detail; for private videos use the owning account)
- Calls POST /video/list/detail  body {"video_id": <number>}
- Downloads the `url` field directly (no-WM when remove_watermark=1)
- Saves to ./downloads/<video_id>.mp4

Importable:
  from pixverse_nwm import download_video
  path = await download_video("413080782435081")
"""
import sys, os, json, re, argparse, asyncio
sys.path.insert(0, '/home/hermes/captcha-solver')
from playwright.async_api import async_playwright

API = "https://app-api.pixverse.ai/creative_platform"
HERE = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(HERE, "pixverse_accounts.txt")
OUTDIR = os.path.join(HERE, "downloads")
SK = "0x4AAAAAAATSS5Nb9KyiA05l"

def pick_account(preferred=None):
    accts = [l.strip().split('|') for l in open(F) if l.strip() and not l.startswith('#')]
    if preferred:
        for a in accts:
            if a[0] == preferred:
                return a[0], a[1], a[2]
    for a in accts:
        if len(a) >= 3 and a[2]:
            return a[0], a[1], a[2]
    raise SystemExit("No account with password found in pixverse_accounts.txt")

def extract_vid(arg):
    m = re.search(r'(\d{10,})', arg)
    return m.group(1) if m else None

async def download_video(vid, account=None):
    """Download a PixVerse video (no-WM) and return local file path."""
    vid = extract_vid(vid)
    if not vid:
        raise ValueError("cannot extract video_id")
    email, username, password = pick_account(account)
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, args=["--no-sandbox","--disable-dev-shm-usage"])
        ctx = await b.new_context()
        pg = await ctx.new_page()
        await pg.goto("https://app.pixverse.ai", wait_until="domcontentloaded", timeout=60000)
        await pg.wait_for_timeout(1500)
        r = await pg.evaluate("""async(a)=>{const r=await fetch(a.url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:a.u,password:a.p})});return{status:r.status,body:await r.text()};}""", {"url":API+"/login","u":username,"p":password})
        body = json.loads(r["body"]) if isinstance(r["body"], str) else r["body"]
        if body.get("ErrCode") != 0:
            await b.close(); raise RuntimeError("login failed: "+str(r.get("body")))
        jwt = body["Resp"]["Result"]["Token"]
        await ctx.add_cookies([{"name":"_ai_token","value":jwt,"url":"https://app.pixverse.ai"}])
        await pg.goto("https://app.pixverse.ai", wait_until="domcontentloaded", timeout=60000)
        await pg.evaluate("""(t)=>document.cookie='_ai_token='+t+';path=/;domain=.pixverse.ai'""", jwt)
        await pg.wait_for_timeout(500)

        rd = await pg.evaluate("""async(a)=>{const r=await fetch(a.u,{method:'POST',headers:{'Content-Type':'application/json','X-Platform':'web','Token':a.t,'Origin':'https://app.pixverse.ai','Referer':'https://app.pixverse.ai/'},body:JSON.stringify({video_id:Number(a.vid)})});return r.status+' '+await r.text();}""", {"u":API+"/video/list/detail","t":jwt,"vid":vid})
        if isinstance(rd, dict):
            raw = rd.get("body", ""); status = rd.get("status")
        else:
            status, raw = rd.split(' ', 1)
        d = json.loads(raw).get("Resp", {}) if isinstance(raw, str) else raw.get("Resp", {})
        url = d.get("url")
        rm = d.get("remove_watermark")
        if not url:
            await b.close(); raise RuntimeError("no url (private or not found)")
        os.makedirs(OUTDIR, exist_ok=True)
        fn = os.path.join(OUTDIR, f"{vid}.mp4")
        dl = await pg.evaluate("""async(a)=>{const r=await fetch(a.url,{headers:{'Referer':'https://app.pixverse.ai/'}});const b=await r.blob();return {status:r.status, size:b.size, data:Array.from(new Uint8Array(await b.arrayBuffer()))};}""", {"url":url})
        if dl.get("status") != 200:
            await b.close(); raise RuntimeError("download failed status "+str(dl.get("status")))
        with open(fn, "wb") as f:
            f.write(bytes(dl["data"]))
        await b.close()
        return fn

async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="video_id or full URL")
    ap.add_argument("--account", default=None)
    args = ap.parse_args()
    fn = await download_video(args.target, args.account)
    print("SAVED ->", fn)

if __name__ == "__main__":
    asyncio.run(main())
