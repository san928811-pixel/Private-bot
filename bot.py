from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ==== YOUR BOT TOKEN ====
TOKEN = "7936792037:AAEY8w1SamKAanqZr66Lbfd_DKUK0GUzC18"

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot successfully चल रहा है!")

# /broadcast command
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = " ".join(context.args)

    if not msg:
        await update.message.reply_text("❌ Broadcast भेजने के लिए:\n/broadcast आपका_मेसेज")
        return

    # Users list (आपका Telegram ID यहाँ होगा)
    users = [7895892794]

    for uid in users:
        try:
            await context.bot.send_message(chat_id=uid, text=msg)
        except:
            pass

    await update.message.reply_text("✅ Broadcast message भेज दिया गया!")

# Run bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))

    app.run_polling()
