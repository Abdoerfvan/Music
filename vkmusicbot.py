import os import uuid import yt_dlp from fastapi import FastAPI from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters import asyncio

FastAPI app for Render

app = FastAPI()

@app.get("/") def home(): return {"status": "Bot is running!"}

Directory for saving music

DOWNLOAD_DIR = "downloads" os.makedirs(DOWNLOAD_DIR, exist_ok=True)

Handle /start

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("Send me a song name and I’ll give you 10 YouTube results to choose from.")

Search YouTube for top 10 results

async def search_youtube(query): ydl_opts = { 'quiet': True, 'skip_download': True, 'extract_flat': True, 'forcejson': True, } results = [] with yt_dlp.YoutubeDL(ydl_opts) as ydl: data = ydl.extract_info(f"ytsearch10:{query}", download=False) for entry in data['entries']: results.append((entry['title'], entry['url'])) return results

Handle song name

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE): query = update.message.text results = await search_youtube(query) if not results: await update.message.reply_text("No results found.") return keyboard = [ [InlineKeyboardButton(title[:50], callback_data=url)] for title, url in results ] await update.message.reply_text("Select the song to download:", reply_markup=InlineKeyboardMarkup(keyboard))

Download audio

async def download_audio(url): filename = os.path.join(DOWNLOAD_DIR, f"{uuid.uuid4()}.mp3") ydl_opts = { 'format': 'bestaudio', 'outtmpl': filename, 'quiet': True, 'postprocessors': [{ 'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192', }], } with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([url]) return filename

Handle button press

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE): query = update.callback_query await query.answer() url = query.data await query.edit_message_text("Downloading your song...")

file_path = await download_audio(url)
await query.message.reply_audio(audio=open(file_path, 'rb'))
os.remove(file_path)

Start the bot in an async loop for Render

async def run_bot(): TOKEN = os.getenv("BOT_TOKEN") if not TOKEN: raise RuntimeError("BOT_TOKEN not set in environment")

app_bot = Application.builder().token(TOKEN).build()
app_bot.add_handler(CommandHandler("start", start))
app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app_bot.add_handler(CallbackQueryHandler(button))

print("Bot is starting...")
await app_bot.run_polling()

Run the bot in the background

@app.on_event("startup") def start_bot(): asyncio.create_task(run_bot())

