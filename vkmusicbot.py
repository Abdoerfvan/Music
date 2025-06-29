import os
import uuid
import yt_dlp
import asyncio

from fastapi import FastAPI
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# FastAPI app instance for Render
app = FastAPI()

@app.get("/")
def home():
    return {"status": "Bot is running!"}

# Directory to save downloaded MP3 files
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Telegram /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send me a song name and I'll give you 10 YouTube results to choose from."
    )

# Function to search YouTube and return top 10 results
async def search_youtube(query):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'extract_flat': True,
        'forcejson': True,
    }
    results = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        data = ydl.extract_info(f"ytsearch10:{query}", download=False)
        for entry in data['entries']:
            results.append((entry['title'], entry['url']))
    return results

# Handle user messages with song names
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    results = await search_youtube(query)
    if not results:
        await update.message.reply_text("No results found.")
        return

    keyboard = [
        [InlineKeyboardButton(title[:50], callback_data=url)]
        for title, url in results
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select the song to download:", reply_markup=reply_markup)

# Download audio as MP3 from YouTube URL
async def download_audio(url):
    filename = os.path.join(DOWNLOAD_DIR, f"{uuid.uuid4()}.mp3")
    ydl_opts = {
        'format': 'bestaudio',
        'outtmpl': filename,
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return filename

# Handle button callback to download and send audio
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    url = query.data
    await query.edit_message_text("Downloading your song...")

    file_path = await download_audio(url)
    with open(file_path, 'rb') as audio_file:
        await query.message.reply_audio(audio=audio_file)
    os.remove(file_path)

# Async function to run the Telegram bot
async def run_bot():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN not set in environment")

    app_bot = Application.builder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app_bot.add_handler(CallbackQueryHandler(button))

    print("Bot is starting...")
    await app_bot.run_polling()

# On startup, launch the bot as a background task in FastAPI
@app.on_event("startup")
def startup_event():
    asyncio.create_task(run_bot())