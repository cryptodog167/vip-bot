import logging
from telegram import Update, ChatPermissions
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import asyncio

# --- CONFIGURATION ---

TOKEN = "7687564005:AAGLOFkYSA_pDj6nXCE11VAJQJzWGc_PaEk"  # Your bot token
VIP_CHANNEL_ID = -1002282793492  # Your VIP channel ID (with -100 prefix)
ADMIN_USER_ID = 250181723  # Your Telegram user ID

# --- SETUP LOGGING ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- VIP USERS TRACKING ---
vip_users = {}  # user_id -> expiration datetime

scheduler = AsyncIOScheduler()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! To get VIP access, please pay and send a screenshot here along with your username."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send your payment screenshot and your Telegram username.")

async def payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text or ""
    photo = update.message.photo

    if photo:
        username = text.strip() if text else update.message.caption or ""
        if not username:
            await update.message.reply_text(
                "Please include your Telegram username with the payment screenshot."
            )
            return

        # Forward message to admin
        await context.bot.send_message(
            chat_id=ADMIN_USER_ID,
            text=f"Payment screenshot from @{user.username} (ID: {user.id})\nUsername provided: {username}",
        )
        await update.message.reply_text(
            "Thank you! Your payment is pending admin approval."
        )
    else:
        await update.message.reply_text(
            "Please send a payment screenshot photo along with your Telegram username."
        )

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("You are not authorized to approve payments.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Usage: /approve <user_id>")
        return

    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("User ID must be an integer.")
        return

    expire_date = datetime.utcnow() + timedelta(days=30)
    vip_users[user_id] = expire_date

    try:
        await context.bot.invite_chat_member(VIP_CHANNEL_ID, user_id)
    except Exception as e:
        logger.error(f"Failed to add user {user_id} to VIP channel: {e}")

    await update.message.reply_text(
        f"User {user_id} approved and added to VIP channel until {expire_date} UTC."
    )

async def remove_expired_users():
    while True:
        now = datetime.utcnow()
        expired = [uid for uid, exp in vip_users.items() if exp < now]

        for user_id in expired:
            try:
                await application.bot.ban_chat_member(VIP_CHANNEL_ID, user_id)
                vip_users.pop(user_id)
                logger.info(f"Removed expired VIP user {user_id}")
            except Exception as e:
                logger.error(f"Error removing user {user_id}: {e}")

        await asyncio.sleep(3600)  # check every hour

if name == "__main__":
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("approve", approve))
    application.add_handler(
        MessageHandler(filters.PHOTO & ~filters.COMMAND, payment_handler)
    )

    scheduler.add_job(remove_expired_users)
    scheduler.start()

    application.run_polling()
