import os
import logging
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Function to sanitize the filename
def sanitize_filename(title):
    return re.sub(r'[<>:"/\\|?*]', '', title)  # Remove invalid characters

async def download_audio(video_url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(id)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'cookiefile': 'cookies.txt',  # Add the path to your cookies.txt file
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            video_title = sanitize_filename(info['title'])  # Sanitize video title
            output_filename = f"{info['id']}.mp3"  # Use video ID for the downloaded file

            # Check if the MP3 file exists after the download process
            if os.path.exists(output_filename):
                logger.info(f"Successfully downloaded: {output_filename}")
                return output_filename, video_title  # Return both the filename and the sanitized title
            else:
                logger.error(f"File not found after download. Expected: {output_filename}")
                return None, None
    except Exception as e:
        logger.error(f"Error during download: {e}")
        return None, None


# Start command to check if the bot is working
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Send me a YouTube link and I will convert it to MP3.')

# Function to handle messages containing a YouTube link
async def process_video_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    video_url = update.message.text.strip()  # Get the full URL

    # Delete the original message
    await context.bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)

    # Send a loading message
    loading_message = await context.bot.send_message(
        chat_id=update.message.chat_id,
        text="Downloading audio... Please wait."
    )

    # Download audio
    audio_file, video_title = await download_audio(video_url)

    if audio_file and video_title:
        # Edit the loading message to indicate completion
        await context.bot.edit_message_text(
            chat_id=update.message.chat_id,
            message_id=loading_message.message_id,
            text="Download complete! Sending audio..."
        )

        # Send the audio to the user with the sanitized title
        with open(audio_file, 'rb') as audio:
            await context.bot.send_audio(chat_id=update.message.chat_id, audio=audio, filename=f"{video_title}.mp3")

        # Clean up downloaded file
        os.remove(audio_file)

        # Delete the loading message after sending the audio
        await context.bot.delete_message(chat_id=update.message.chat_id, message_id=loading_message.message_id)
    else:
        # Handle download error
        logger.error("An error occurred while downloading the audio.")
        await context.bot.edit_message_text(
            chat_id=update.message.chat_id,
            message_id=loading_message.message_id,
            text="An error occurred while downloading the audio."
        )

# Main function to start the bot
def main():
    # Your bot token here
    BOT_TOKEN = os.getenv('BOT_TOKEN')

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Start command
    app.add_handler(CommandHandler("start", start))

    # Handle any text message (assumes it's a YouTube link)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_video_selection))

    # Start the bot
    app.run_polling()

if __name__ == '__main__':
    main()
