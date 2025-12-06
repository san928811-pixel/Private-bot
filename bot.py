import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# YOUR BOT TOKEN
TOKEN = "YOUR_BOT_TOKEN_HERE"

# जिन users को broadcast भेजना है
USERS = [7895892794]   # यहाँ अपनी Telegram ID डालो

# Logs enable
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot सफलतापूर्वक चल रहा है!")


# /broadcast command
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = " ".join(context.args)

    if not msg:
        await update.message.reply_text("❗ Broadcast भेजने के लिए: /broadcast आपका_मेसेज")
        return

    for user in USERS:
        try:
            await context.bot.send_message(chat_id=user, text=msg)
        except:
            pass

    await update.message.reply_text("✔️ Message भेज दिया गया!")


# MAIN FUNCTION
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))

    print("BOT IS RUNNING...")
    await app.run_polling()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
