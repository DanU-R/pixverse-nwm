# pixverse-nwm

Download PixVerse video **tanpa watermark** — **TANPA LOGIN**.

## Cara kerja
Buka halaman public `app.pixverse.ai/video/<id>` headless, ambil `<video>` src
(`/ori/` URL = file clean no-WM), lalu download via curl.

## Usage
```
python pixverse_nwm.py <video_id_or_url>
```
Contoh:
```
python pixverse_nwm.py https://app.pixverse.ai/video/413080782435081
```
Output: `downloads/<video_id>.mp4`

## Catatan
- Works untuk **video public**. Video private (cuma si empunya) ga ke-scrape.
- No account / no API token needed.

## Deps
```
pip install playwright
playwright install chromium
```
