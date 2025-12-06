from telegram.ext import Updater, CommandHandler

TOKEN = "7936792037:AAEY8w1SamKAanqZr66Lbfd_DKUK0GUzC18"

def start(update, context):
    update.message.reply_text("Bot chal raha hai! 🔥")

def broadcast(update, context):
    msg = " ".join(context.args)
    if not msg:
        update.message.reply_text("Kya bhejunga? Message likho.")
        return

    users = [7895892794]  # Apni Telegram ID
    for u in users:
        try:
            context.bot.send_message(chat_id=u, text=msg)
        except:
            pass

    update.message.reply_text("Message sabko bhej diya! ✔")

updater = Updater(TOKEN, use_context=True)
dp = updater.dispatcher

dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("broadcast", broadcast))

updater.start_polling()
updater.idle()
