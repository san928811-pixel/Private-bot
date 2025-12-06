from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "7936792037:AAEY8w1SamKAanqZr66Lbfd_DKUK0GUzC18"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is working! 👋")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = " ".join(context.args)
    if not msg:
        await update.message.reply_text("❌ Message empty")
        return
    
    # Yahan aap apni user list add karoge
    users = [7895892794]  # Apni Telegram ID

    for u in users:
        try:
            await context.bot.send_message(chat_id=u, text=msg)
        except:
            pass

    await update.message.reply_text("Message sent! ✅")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("broadcast", broadcast))

app.run_polling()
