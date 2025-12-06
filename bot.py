from telegram.ext import Updater, CommandHandler
# ---- YOUR BOT TOKEN ----
TOKEN = "7936792037:AAEY8w1SamKAanqZr66Lbfd_DKUK0GUzC18"

# ---- /start command ----
def start(update, context):
    update.message.reply_text("Bot सफलतापूर्वक चल रहा है ✔️")

# ---- /broadcast command ----
def broadcast(update, context):
    msg = " ".join(context.args)

    if not msg:
        update.message.reply_text("❗ Broadcast भेजने के लिए: /broadcast आपका_मैसेज")
        return

    # जिन users को message भेजना है उनकी list
    users = [7895892794]   # यहाँ अपनी Telegram ID डालो

    for u in users:
        try:
            context.bot.send_message(chat_id=u, text=msg)
        except:
            pass

    update.message.reply_text("✔️ Message भेज दिया गया")

# ---- RUN BOT ----
updater = Updater(TOKEN, use_context=True)
dp = updater.dispatcher

dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("broadcast", broadcast))

updater.start_polling()
updater.idle()
