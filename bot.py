from telegram.ext import Updater, CommandHandler

# --- Your Bot Token ---
TOKEN = "7936792037:AAEY8w1SamKAanqZr66Lbfd_DKUK0GUzC18"

# /start command
def start(update, context):
    update.message.reply_text("Bot chal raha hai! 👋")

# /broadcast command
def broadcast(update, context):
    msg = " ".join(context.args)
    if not msg:
        update.message.reply_text("Kya message bhejna hai?")
        return

    # Sirf un logon ko message bhejega jinko aap list me add karoge
    users = [7895892794]   # <-- Apna Telegram User ID

    for u in users:
        try:
            context.bot.send_message(chat_id=u, text=msg)
        except:
            pass

    update.message.reply_text("Message successfully broadcast ho gaya! ✅")

# --- Run Application ---
updater = Updater(TOKEN, use_context=True)
dp = updater.dispatcher

dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("broadcast", broadcast))

updater.start_polling()
updater.idle()
