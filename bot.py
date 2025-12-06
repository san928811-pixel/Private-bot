from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "7936792037:AAEY8w1SamKAanqZr66Lbfd_DKUK0GUzC18"   # NEW TOKEN

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot chal raha hai! 👌")

# /broadcast command
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = " ".join(context.args)

    if not msg:
        await update.message.reply_text("Broadcast message likho!")
        return

    # Yahan un users ki list jinko message bhejna hai
    users = [7895892794]   # Yahan tumhari Telegram ID

    for u in users:
        try:
            await context.bot.send_message(chat_id=u, text=msg)
        except:
            pass

    await update.message.reply_text("Message broadcast ho gaya. ✔")

# --- Application run ---
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("broadcast", broadcast))

app.run_polling()
