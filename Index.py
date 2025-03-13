from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv
import yt_dlp
import os
import asyncio

# Load environment variables from .env file
load_dotenv()

# Retrieve the bot token from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Dictionary to track ongoing downloads
download_tasks = {}

# Function to search YouTube for songs
def search_youtube(query):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'noplaylist': True,
        'extract_flat': 'in_playlist',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        search_results = ydl.extract_info(f"ytsearch5:{query}", download=False)['entries']
    return search_results

# Asynchronous function to download audio
async def download_audio(url, title, chat_id):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{title}.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128',
        }],
        'quiet': True,
    }

    loop = asyncio.get_event_loop()
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        task = loop.run_in_executor(None, ydl.download, [url])
        download_tasks[chat_id] = task
        try:
            await task
        except asyncio.CancelledError:
            # Delete partial file if download is canceled
            if os.path.exists(f"{title}.mp3"):
                os.remove(f"{title}.mp3")
            raise

# Handle the /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! Send me the name of the song you want to search 🎵")

# Handle song search
async def search_song(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    results = search_youtube(query)

    if not results:
        await update.message.reply_text("No songs found. Try another name.")
        return

    # Create inline buttons for song choices
    buttons = [
        [InlineKeyboardButton(result['title'], callback_data=result['url'])]
        for result in results
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    await update.message.reply_text("Select a song to download:", reply_markup=reply_markup)

# Handle button press and start download
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    url = query.data
    title = url.split('=')[-1]
    chat_id = query.message.chat_id

    # Send cancel button
    cancel_button = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancel Download", callback_data=f"cancel_{chat_id}")]
    ])
    await query.edit_message_text(text="Downloading your song... 🎶", reply_markup=cancel_button)

    try:
        await download_audio(url, title, chat_id)
        audio_file = f"{title}.mp3"

        if os.path.exists(audio_file):
            file_size = os.path.getsize(audio_file)

            if file_size <= 50 * 1024 * 1024:
                await context.bot.send_audio(chat_id=chat_id, audio=open(audio_file, 'rb'))
            else:
                await context.bot.send_document(chat_id=chat_id, document=open(audio_file, 'rb'))

            os.remove(audio_file)
        else:
            await query.edit_message_text(text="Failed to download the song. Try again.")

    except asyncio.CancelledError:
        await context.bot.send_message(chat_id=chat_id, text="🚫 Download canceled.")
    finally:
        download_tasks.pop(chat_id, None)

# Handle cancel download
async def cancel_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = int(query.data.split('_')[1])

    task = download_tasks.get(chat_id)
    if task:
        task.cancel()
        await query.edit_message_text(text="Canceling download... 🚫")
    else:
        await query.edit_message_text(text="No active download to cancel.")

# Main function to run the bot
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_song))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(?!cancel_).*"))
    app.add_handler(CallbackQueryHandler(cancel_download, pattern="^cancel_"))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
