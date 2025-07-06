# Telegram Music Bot 🎵

A Telegram bot that downloads and sends songs with cover art using YouTube.

## Features
- 🎧 /song command to get music
- 🖼️ Sends embedded album art
- 🕓 Rate limiting per user
- ⚙️ Uses yt-dlp + FFmpeg

## Setup
1. Add your bot token to `main.py`
2. Install dependencies: `pip install -r requirements.txt`
3. Place `ffmpeg.exe` and `ffprobe.exe` in `ffmpeg/bin/`
4. Run the bot: `python main.py`
