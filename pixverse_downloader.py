#!/usr/bin/env python3
"""
PixVerse Downloader — Download video & image tanpa watermark
Support: T2V, I2V, I2I, T2I
Tidak perlu login/API key
"""
import requests, re, sys, os
from urllib.parse import unquote

def fetch_page(url):
    """Fetch PixVerse page HTML"""
    r = requests.get(url, 
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        },
        timeout=30)
    r.raise_for_status()
    return r.text

def extract_media(html):
    """Extract semua media URLs dari HTML"""
    # Pattern: https://media.pixverse.ai/pixverse/...
    matches = re.findall(r'(https://media\.pixverse\.ai/pixverse[^"\'\s>]+)', html)
    
    results = []
    for m in matches:
        # Decode URL encoding
        m = unquote(m)
        
        # Skip duplicates
        if m in [r['url'] for r in results]:
            continue
        
        # Categorize
        if '/mp4/' in m and m.endswith('.mp4'):
            results.append({
                'type': 'video',
                'subtype': 't2v' if 'media/web' in m else m.split('/ori/')[-1].split('_')[0],
                'url': m,
                'filename': m.split('/')[-1]
            })
        elif '/i2i/' in m and m.endswith(('.jpg', '.jpeg', '.png')):
            results.append({
                'type': 'image',
                'subtype': 'i2i',
                'url': m,
                'filename': m.split('/')[-1]
            })
        elif '/frame/' in m and m.endswith('.jpg'):
            results.append({
                'type': 'thumbnail',
                'url': m,
                'filename': m.split('/')[-1]
            })
    
    return results

def download_file(url, output_dir="."):
    """Download file dengan progress bar"""
    os.makedirs(output_dir, exist_ok=True)
    
    filename = url.split('/')[-1]
    filepath = os.path.join(output_dir, filename)
    
    print(f"[*] Downloading: {filename[:60]}...")
    
    r = requests.get(url, stream=True, timeout=120)
    r.raise_for_status()
    
    total = int(r.headers.get('content-length', 0))
    downloaded = 0
    
    with open(filepath, 'wb') as f:
        for chunk in r.iter_content(chunk_size=16384):
            f.write(chunk)
            downloaded += len(chunk)
            if total:
                pct = downloaded / total * 100
                print(f"\r[*] {pct:.1f}% ({downloaded/1024/1024:.1f}MB/{total/1024/1024:.1f}MB)", end='', flush=True)
    
    if not total:
        size = os.path.getsize(filepath)
        print(f"\r[*] Downloaded: {size/1024/1024:.1f}MB", flush=True)
    else:
        print(f"\r[*] 100.0% ({downloaded/1024/1024:.1f}MB)", flush=True)
    
    print(f"[+] Saved: {filepath}")
    return filepath

def main():
    if len(sys.argv) < 2:
        print("PixVerse Downloader — Download tanpa watermark")
        print()
        print("Usage: python3 pixverse_downloader.py <url>")
        print()
        print("Examples:")
        print("  python3 pixverse_downloader.py https://app.pixverse.ai/video/413374824236288")
        print("  python3 pixverse_downloader.py https://app.pixverse.ai/image/413281468716964")
        print()
        print("Output:")
        print("  - Video: .mp4 (no watermark)")
        print("  - Image: .jpg (no watermark)")
        print("  - Thumbnail: .jpg (preview)")
        sys.exit(1)
    
    page_url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "."
    
    print(f"[*] Fetching: {page_url}")
    html = fetch_page(page_url)
    
    media = extract_media(html)
    
    if not media:
        print("[!] No media found")
        print("[*] Page HTML preview:")
        print(html[:500])
        sys.exit(1)
    
    print(f"[+] Found {len(media)} media items:")
    for i, item in enumerate(media, 1):
        print(f"  {i}. [{item['type']}]{item.get('subtype','')} — {item['filename'][:60]}")
    
    print(f"\n[*] Downloading to: {output_dir}/")
    downloaded = []
    
    for item in media:
        if item['type'] in ['video', 'image']:  # Skip thumbnails
            try:
                fp = download_file(item['url'], output_dir)
                downloaded.append(fp)
            except Exception as e:
                print(f"[!] Failed: {item['filename']} — {e}")
    
    print(f"\n{'='*50}")
    print(f"[✓] DONE — {len(downloaded)} files downloaded")
    for fp in downloaded:
        print(f"  {fp}")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
