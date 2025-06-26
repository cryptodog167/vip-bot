import logging
from telegram import Update, ChatPermissions
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import os

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "7687564005:AAGLOFkYSA_pDj6nXCE11VAJQJzWGc_PaEk")
ADMIN_ID = 250181723
VIP_CHANNEL_ID = -1002282793492

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dictionary to store approved users and their expiration times
approved_users = {}

# Scheduler for removing users after 30 days
scheduler = BackgroundScheduler()
scheduler.start()

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome! To access the VIP channel, please:\n\n"
        "1️⃣ Send a screenshot of your payment.\n"
        "2️⃣ Send your Telegram username (e.g. @yourusername).\n\n"
        "💳 Payment address:\n1234567890\n\n"
        "Your request will be reviewed shortly. Thank you!"
    )

# Handle photo (payment screenshot)
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    caption = update.message.caption or ""
    file_id = update.message.photo[-1].file_id

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=file_id,
        caption=f"🧾 New payment screenshot from @{user.username or user.first_name} ({user.id})\n\nCaption: {caption}",
    )

# Handle text (username)
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    message = update.message.text

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📨 New message from @{user.username or user.first_name} ({user.id}):\n{message}",
    )

# Approve command (used by admin manually)
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ You are not authorized to use this command.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Usage: /approve <user_id>")
        return

    try:
        user_id = int(context.args[0])
        expiration = datetime.now() + timedelta(days=30)

        await context.bot.invite_chat_member(chat_id=VIP_CHANNEL_ID, user_id=user_id)
        approved_users[user_id] = expiration

        await update.message.reply_text(f"✅ User {user_id} has been added to the VIP channel for 30 days.")

        # Schedule automatic removal
        scheduler.add_job(
            remove_user,
            'date',
            run_date=expiration,
            args=[context.bot, user_id],
        )

    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

# Remove user function
async def remove_user(bot, user_id):
    try:
        await bot.ban_chat_member(chat_id=VIP_CHANNEL_ID, user_id=user_id)
        await bot.unban_chat_member(chat_id=VIP_CHANNEL_ID, user_id=user_id)
        logger.info(f"✅ User {user_id} has been removed after 30 days.")
    except Exception as e:
        logger.error(f"❌ Failed to remove user {user_id}: {e}")

# Main
if name == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("🤖 Bot is running...")
    app.run_polling()
