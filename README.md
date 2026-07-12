# pixverse-nwm

Download PixVerse video **tanpa watermark** via API.

## Cara kerja
- Login via akun PixVerse (`pixverse_accounts.txt`)
- `POST /video/list/detail` body `{"video_id": <number>}`
- Download field `url` langsung (no-WM kalau `remove_watermark:1`)

## Usage
```
python pixverse_nwm.py <video_id_or_url> [--account user@domain]
```
Contoh:
```
python pixverse_nwm.py https://app.pixverse.ai/video/413080782435081
```
Output: `downloads/<video_id>.mp4`

## Deps
```
pip install playwright
playwright install chromium
```
Butuh `pixverse_accounts.txt` (format: `email|username|password`) — tidak diinclude (rahasia).
