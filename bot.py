from telegram import Update, ChatPermissions
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from apscheduler.schedulers.background import BackgroundScheduler
import datetime

TOKEN = '7687564005:AAGLOFkYSA_pDj6nXCE11VAJQJzWGc_PaEk'
ADMIN_ID = 250181723
VIP_CHANNEL_ID = -1002282793492
PAYMENT_INFO = 'Please pay via BINANCE: crypto_user123\nSend your payment screenshot and username here.'

vip_users = {}
scheduler = BackgroundScheduler()

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    context.bot.send_message(chat_id=user.id, text=f"Hello @{user.username or user.id},\n{PAYMENT_INFO}")

def handle_photo(update: Update, context: CallbackContext):
    user = update.effective_user
    if update.message.photo:
        context.bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id,
                               caption=f"⬆️ Payment screenshot from @{user.username or user.id}\n🆔 ID: {user.id}")
        context.bot.send_message(chat_id=user.id, text="Payment received. Please wait for confirmation.")
    else:
        context.bot.send_message(chat_id=user.id, text="Please send your payment screenshot as a photo.")

def approve(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("⛔ You don't have permission to use this command.")
        return
    if len(context.args) != 1:
        update.message.reply_text("Usage: /approve USER_ID")
        return

    user_id = int(context.args[0])
    until = datetime.datetime.now() + datetime.timedelta(days=30)
    vip_users[user_id] = until

    try:
        context.bot.invite_chat_member(chat_id=VIP_CHANNEL_ID, user_id=user_id)
        update.message.reply_text(f"✅ User {user_id} has been added to the VIP channel for 30 days.")
    except Exception as e:
        update.message.reply_text(f"❌ Failed to add user: {e}")

def remove_expired():
    now = datetime.datetime.now()
    for user_id in list(vip_users.keys()):
        if vip_users[user_id] < now:
            try:
                updater.bot.kick_chat_member(chat_id=VIP_CHANNEL_ID, user_id=user_id)
                del vip_users[user_id]
            except Exception as e:
                print(f"❌ Error removing user: {e}")

def main():
    global updater
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("approve", approve))
    dp.add_handler(MessageHandler(Filters.photo & (~Filters.command), handle_photo))

    scheduler.add_job(remove_expired, 'interval', hours=1)
    scheduler.start()

    updater.start_polling()
    updater.idle()

if name == '__main__':
    main()
