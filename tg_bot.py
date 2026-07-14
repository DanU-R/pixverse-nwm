#!/usr/bin/env python3
"""
tg_bot.py - Telegram bot: send a PixVerse video OR image link, get the no-WM
MP4 / image back.

Run:
  BOT_TOKEN=xxxx python tg_bot.py
  (or export BOT_TOKEN)

Flow:
  user sends: https://app.pixverse.ai/video/413080782435081
    -> download_video() -> reply MP4 (no-WM)
  user sends: https://app.pixverse.ai/image/413080782435081
    -> download_image() -> reply photo (no-WM)
  Public videos/images only.
"""
import os, sys, re, logging
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import pixverse_downloader as pdl

def extract_vid(text):
    m = re.search(r'(\d{10,})', text)
    return m.group(1) if m else None

def get_kind(text):
    """Return 'image' or 'video' based on URL hint, default 'video'."""
    if "/image/" in text or "pixverse.ai/image" in text:
        return "image"
    return "video"

def _build_url(text):
    """Reconstruct full PixVerse page URL from the user's link."""
    return text.strip()

def download_video(text):
    """Fetch video page, extract no-WM mp4, return local filepath."""
    html = pdl.fetch_page(_build_url(text))
    media = pdl.extract_media(html)
    vids = [m for m in media if m['type'] == 'video']
    if not vids:
        raise RuntimeError("no video found on page")
    return pdl.download_file(vids[0]['url'], "/tmp")

def download_image(text):
    """Fetch image page, extract no-WM image, return local filepath."""
    html = pdl.fetch_page(_build_url(text))
    media = pdl.extract_media(html)
    imgs = [m for m in media if m['type'] == 'image']
    if not imgs:
        raise RuntimeError("no image found on page")
    return pdl.download_file(imgs[0]['url'], "/tmp")

async def start(update: Update, context):
    await update.message.reply_text(
        "Kirim link PixVerse (video atau image), contoh:\n"
        "Video: https://app.pixverse.ai/video/413080782435081\n"
        "Image: https://app.pixverse.ai/image/413080782435081\n"
        "Bot download tanpa watermark lalu kirim file."
    )

async def handle(update: Update, context):
    msg = update.message.text or ""
    vid = extract_vid(msg)
    if not vid:
        await update.message.reply_text("Link ga valid. Kirim link PixVerse video/image.")
        return
    kind = get_kind(msg)
    await update.message.reply_text(f"Downloading {kind} {vid} tanpa watermark... (40-90 detik)")
    try:
        if kind == "image":
            fn = download_image(msg)  # full page URL
            size = os.path.getsize(fn)
            if size > 10 * 1024 * 1024:
                await update.message.reply_document(document=open(fn, "rb"), caption=f"Image {vid} (no-WM)")
            else:
                await update.message.reply_photo(photo=open(fn, "rb"), caption=f"Image {vid} (no-WM)")
        else:
            fn = download_video(msg)  # full page URL
            size = os.path.getsize(fn)
            if size > 50 * 1024 * 1024:
                await update.message.reply_document(document=open(fn, "rb"), caption=f"Video {vid} (no-WM)")
            else:
                await update.message.reply_video(video=open(fn, "rb"), caption=f"Video {vid} (no-WM)")
    except Exception as e:
        logger.exception("download failed")
        await update.message.reply_text(f"Gagal: {e}")

def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("ERROR: set BOT_TOKEN env var"); sys.exit(1)
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print("Bot running. Send a PixVerse link.")
    app.run_polling()

if __name__ == "__main__":
    main()
