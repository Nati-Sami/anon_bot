import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

# Handler for /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome! Send me any message and it will be forwarded anonymously to the admin. ቃኡን ኣነባለው!"
    )

# Handler for all text messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    # Forward anonymously to the owner
    await context.bot.send_message(chat_id=OWNER_ID, text=f"📨 Anonymous message:\n\n{message}")
    # Confirm to sender
    await update.message.reply_text("✅ Message sent anonymously!")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))  # /start command
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))  # Messages

    app.run_polling()

if __name__ == "__main__":
    main()
