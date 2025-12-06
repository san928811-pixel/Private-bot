from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "7936792037:AAEY8w1SamKAanqZr66Lbfd_DKUK0GUzC18"   # ← यहाँ अपना Bot Token डालो

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✔️ Bot चल रहा है भाई 🙂")

# /broadcast command
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = " ".join(context.args)

    if not msg:
        await update.message.reply_text("⚠️ Message लिखकर भेजें: /broadcast hello")
        return

    # उन users की list जिनको message भेजना है
    users = [7895892794]     # ← यहाँ अपना Telegram ID डालो

    for uid in users:
        try:
            await context.bot.send_message(chat_id=uid, text=msg)
        except:
            pass

    await update.message.reply_text("✔️ Broadcast message भेज दिया गया!")

# RUN BOT
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("broadcast", broadcast))

app.run_polling()
