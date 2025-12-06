from telegram.ext import Updater, CommandHandler

# YOUR BOT TOKEN
TOKEN = "xxxxxxxx"

def start(update, context):
    update.message.reply_text("Bot सफलतापूर्वक चल रहा है ✔️")

def broadcast(update, context):
    msg = " ".join(context.args)
    if not msg:
        update.message.reply_text("❗Broadcast भेजने के लिए /broadcast text")
        return

    users = [7895892794]
    for u in users:
        try:
            context.bot.send_message(chat_id=u, text=msg)
        except:
            pass

    update.message.reply_text("✔️ Message भेज दिया गया")

updater = Updater(TOKEN, use_context=True)
dp = updater.dispatcher

dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("broadcast", broadcast))

updater.start_polling()
updater.idle()
