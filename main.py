import os
import requests
import subprocess
import time
from io import BytesIO
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
import yt_dlp

# === CONFIG ===
BOT_TOKEN = "7744670633:AAHIFI2KY_vOTRnLFcRN470xddf2qigyng8"
DOWNLOAD_DIR = "downloads"
RATE_LIMIT_SECONDS = 30
user_cooldowns = {}

# === FFmpeg Path for Render (Linux)
def get_ffmpeg_path():
    return "ffmpeg"

# === Embed Thumbnail using FFmpeg
def embed_thumbnail_ffmpeg(mp3_path, thumb_path):
    ffmpeg = get_ffmpeg_path()
    output_path = mp3_path.replace(".mp3", "_cover.mp3")

    cmd = [
        ffmpeg, "-y",
        "-i", mp3_path,
        "-i", thumb_path,
        "-map", "0:a", "-map", "1:v",
        "-c:a", "libmp3lame", "-b:a", "192k",
        "-c:v", "mjpeg",
        "-id3v2_version", "3",
        output_path
    ]

    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if os.path.exists(output_path):
        os.remove(mp3_path)
        os.rename(output_path, mp3_path)

# === Download Song with Metadata
def download_audio(query):
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best',
        'noplaylist': True,
        'ignoreerrors': True,
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
        'ffmpeg_location': get_ffmpeg_path(),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch1:{query}", download=True)
        entry = info['entries'][0]
        filepath = ydl.prepare_filename(entry).rsplit('.', 1)[0] + '.mp3'

        title = entry.get('title', 'Unknown Title')
        artist = entry.get('uploader', 'Unknown Artist')
        duration = entry.get('duration', 0)
        thumbnail_url = entry.get('thumbnail')
        thumb_path = None

        if thumbnail_url:
            try:
                res = requests.get(thumbnail_url, timeout=15)
                if res.status_code == 200:
                    thumb_path = os.path.join(DOWNLOAD_DIR, "thumb.jpg")
                    with open(thumb_path, 'wb') as f:
                        f.write(res.content)
                    embed_thumbnail_ffmpeg(filepath, thumb_path)
            except Exception:
                pass

        return filepath, title, artist, duration, thumb_path

# === Start Command Handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["🎵 Send a song"], ["ℹ️ Help", "📋 Menu"]]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("👋 Hello! What would you like to do?", reply_markup=markup)

# === /song Command Handler with Rate Limit & Streaming
async def song(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now = time.time()

    if user_id in user_cooldowns and now - user_cooldowns[user_id] < RATE_LIMIT_SECONDS:
        wait = int(RATE_LIMIT_SECONDS - (now - user_cooldowns[user_id]))
        await update.message.reply_text(f"⏳ Please wait {wait}s before requesting another song.")
        return

    user_cooldowns[user_id] = now

    query = ' '.join(context.args)
    if not query:
        await update.message.reply_text("Usage: /song <song name>")
        return

    await update.message.reply_text("🔎 Ruko dhund raha hu...")

    try:
        filepath, title, artist, duration, thumb_path = download_audio(query)
        caption = f"🎵 *{title}*\n👤 {artist}\n⏱️ {duration // 60}:{duration % 60:02d}"

        with open(filepath, 'rb') as a:
            audio_io = BytesIO(a.read())
            audio_io.name = os.path.basename(filepath)

            await context.bot.send_audio(
                chat_id=update.effective_chat.id,
                audio=audio_io,
                title=title,
                performer=artist,
                caption=caption,
                parse_mode='Markdown'
            )

        os.remove(filepath)
        if thumb_path:
            os.remove(thumb_path)

    except Exception as e:
        await update.message.reply_text(f" Failed to get song:\n{e}", parse_mode='Markdown')

# === Message Handlers
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.lower()
    if "song" in msg:
        await update.message.reply_text("🎶 Bolo Konsa Gaana Chahiye /song <name>")
    elif "help" in msg:
        await update.message.reply_text("ℹ️ Use /song <name> to download music.")
    elif "menu" in msg:
        await update.message.reply_text("📋 Commands:\n/start\n/song <name>\n/help")
    else:
        await update.message.reply_text("🤖 Sahi Command Do. Use /start to see options.")

# === Bot Setup
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("song", song))
app.add_handler(CommandHandler("help", handle_message))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Bot is running...")
app.run_polling()
