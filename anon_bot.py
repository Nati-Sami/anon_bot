# requirements: pip install python-telegram-bot==13.15
from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from datetime import datetime
import os
import json

BOT_TOKEN = os.environ.get("8306130636:AAFBv5JO_TrKOTM3AGD8C7ykheadafRFua4")
ADMIN_STORE = "admin.json"           # stores admin chat_id only
SUBMISSIONS_FILE = "anon_messages.txt"  # stores message content + timestamp (no sender id)

def load_admin():
    if not os.path.exists(ADMIN_STORE):
        return None
    try:
        with open(ADMIN_STORE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("admin_chat_id")
    except Exception:
        return None

def save_admin(chat_id):
    with open(ADMIN_STORE, "w", encoding="utf-8") as f:
        json.dump({"admin_chat_id": chat_id}, f)

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Hi — this bot collects anonymous messages.\n\n"
        "If you're the admin who should receive submissions, send /setadmin now (from your private chat with the bot).\n\n"
        "Everyone else: send your message privately to this bot and it will be delivered anonymously to the admin."
    )

def setadmin(update: Update, context: CallbackContext):
    # Only allow setting admin via private chat
    if update.message.chat.type != "private":
        update.message.reply_text("Please send /setadmin in a private chat with the bot.")
        return

    admin_id = update.message.chat.id
    save_admin(admin_id)
    update.message.reply_text("✅ You are now registered as the admin. You will receive anonymous submissions here.")
    print(f"[INFO] Admin set to chat_id={admin_id}")

def handle_private_message(update: Update, context: CallbackContext):
    # ensure this is a private message
    if update.message.chat.type != "private":
        return

    admin_chat_id = load_admin()
    # If the sender is the admin and they send /getcount or other commands, ignore here
    # We treat messages from admin as normal submissions only if admin hasn't set themselves.
    # For simplicity: don't allow admin to submit anonymously to themselves.
    if admin_chat_id and update.message.chat.id == admin_chat_id:
        # If admin sends plain text and it starts with /, it's a command; otherwise ignore to avoid self-submits
        if update.message.text and update.message.text.startswith("/"):
            return
        update.message.reply_text("You are the admin. Use /start, /export or other admin commands.")
        return

    # Prepare a timestamped, anonymous record
    timestamp = datetime.utcnow().isoformat() + "Z"
    # Get a textual representation of the message (text, caption for media, or a short placeholder)
    if update.message.text:
        content = update.message.text
        kind = "text"
    elif update.message.photo:
        # send note about photo (do not record sender id)
        content = "(photo) " + (update.message.caption or "")
        kind = "photo"
    elif update.message.voice:
        content = "(voice message) " + (update.message.caption or "")
        kind = "voice"
    elif update.message.document:
        content = "(document) " + (update.message.caption or "")
        kind = "document"
    elif update.message.video:
        content = "(video) " + (update.message.caption or "")
        kind = "video"
    else:
        content = "(other media)"
        kind = "other"

    # Save to submissions file (no user id or username)
    with open(SUBMISSIONS_FILE, "a", encoding="utf-8") as f:
        f.write(f"---\n{timestamp}\n{kind}\n{content}\n")

    # Acknowledge to submitter
    update.message.reply_text("✅ Message received anonymously. Thank you!")

    # Forward (as anonymous) to admin if set. For media we forward the file id to admin
    if admin_chat_id:
        try:
            header = f"📨 *Anonymous submission* — {timestamp}"
            if kind == "text" or (kind != "text" and update.message.caption):
                # For text or media with caption, include text/caption
                # Do not include any sender metadata
                if kind == "text":
                    context.bot.send_message(chat_id=admin_chat_id, text=f"{header}\n\n{content}", parse_mode=ParseMode.MARKDOWN)
                else:
                    # For media types include the media itself if possible
                    if kind == "photo":
                        file_id = update.message.photo[-1].file_id
                        context.bot.send_photo(chat_id=admin_chat_id, photo=file_id, caption=header + ("\n\n" + (update.message.caption or "")))
                    elif kind == "voice":
                        file_id = update.message.voice.file_id
                        context.bot.send_voice(chat_id=admin_chat_id, voice=file_id, caption=header)
                    elif kind == "document":
                        file_id = update.message.document.file_id
                        context.bot.send_document(chat_id=admin_chat_id, document=file_id, caption=header)
                    elif kind == "video":
                        file_id = update.message.video.file_id
                        context.bot.send_video(chat_id=admin_chat_id, video=file_id, caption=header)
                    else:
                        context.bot.send_message(chat_id=admin_chat_id, text=f"{header}\n\n{content}", parse_mode=ParseMode.MARKDOWN)
            else:
                context.bot.send_message(chat_id=admin_chat_id, text=f"{header}\n\n{content}", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            print("Failed to notify admin:", e)

def export_submissions(update: Update, context: CallbackContext):
    # Allow only admin to export
    admin_chat_id = load_admin()
    if update.message.chat.id != admin_chat_id:
        update.message.reply_text("Only the registered admin can export submissions.")
        return

    if not os.path.exists(SUBMISSIONS_FILE):
        update.message.reply_text("No submissions yet.")
        return

    # Send the file to admin privately
    with open(SUBMISSIONS_FILE, "rb") as f:
        update.message.reply_document(document=f, filename="anon_messages.txt")
    # Optionally also say how many submissions (count by separators)
    with open(SUBMISSIONS_FILE, "r", encoding="utf-8") as f:
        data = f.read()
    count = data.count("---")
    update.message.reply_text(f"Exported {count} submissions.")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("setadmin", setadmin))
    dp.add_handler(CommandHandler("export", export_submissions))
    dp.add_handler(MessageHandler(Filters.chat_type.private, handle_private_message))

    updater.start_polling()
    print("Bot running...")
    updater.idle()

if __name__ == "__main__":
    main()
