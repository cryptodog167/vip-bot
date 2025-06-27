import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime, timedelta
import asyncio

# Configurations
BOT_TOKEN = "7687564005:AAGLOFkYSA_pDj6nXCE11VAJQJzWGc_PaEk"
ADMIN_ID = 250181723  # შენი Telegram ID (ადმინისტრატორი)
VIP_CHANNEL_ID = -1002282793492  # შენი VIP არხის ID

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

approved_users = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! Please send your payment screenshot (photo or document).")

async def handle_payment_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if update.message.photo or update.message.document:
        # Forward payment screenshot to admin
        await context.bot.forward_message(chat_id=ADMIN_ID, from_chat_id=update.message.chat_id, message_id=update.message.message_id)
        await update.message.reply_text("Payment screenshot received. Please wait for approval.")
    else:
        await update.message.reply_text("Please send a photo or document as payment proof.")

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Usage: /approve <user_id>")
        return

    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid user ID.")
        return

    expire_date = datetime.now() + timedelta(days=30)
    approved_users[user_id] = expire_date

    try:
        # Add user to VIP channel
        await context.bot.invite_chat_member(chat_id=VIP_CHANNEL_ID, user_id=user_id)
    except Exception as e:
        logging.error(f"Error adding user to VIP channel: {e}")

    await update.message.reply_text(f"User {user_id} approved until {expire_date.strftime('%Y-%m-%d')}")

    # Schedule removal after 30 days
    asyncio.create_task(remove_user_after_30_days(context, user_id))

async def remove_user_after_30_days(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    await asyncio.sleep(30 * 24 * 3600)  # 30 days in seconds
    try:
        await context.bot.ban_chat_member(chat_id=VIP_CHANNEL_ID, user_id=user_id)
        await context.bot.unban_chat_member(chat_id=VIP_CHANNEL_ID, user_id=user_id)
        logging.info(f"User {user_id} removed from VIP channel after 30 days.")
    except Exception as e:
        logging.error(f"Error removing user from VIP channel: {e}")

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_payment_screenshot))
    app.add_handler(CommandHandler("approve", approve))

    await app.run_polling()

if name == '__main__':
    import asyncio
    asyncio.run(main())
