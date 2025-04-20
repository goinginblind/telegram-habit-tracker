from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "7773979061:AAHDsdKNNT34QfhghscWNOU6qgkYQBmSVLs"
NGROK_URL = "https://6db2-45-85-105-105.ngrok-free.app"  # your HTTPS frontend URL

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Open Habit Tracker", web_app=WebAppInfo(url=NGROK_URL))]
    ])
    await update.message.reply_text(
        "Hi! Click the button below to open your habit tracker:",
        reply_markup=keyboard
    )

def main():
    print("Bot is running")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == "__main__":
    main()
