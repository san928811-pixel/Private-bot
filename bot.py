import json
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

BOT_TOKEN = "7936792037:AAEY8w1SamKAanqZr66Lbfd_DKUK0GUzC18"
OWNER_ID = 7895892794  # Your Telegram ID

DATA_FILE = "users.json"

def load_users():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_users(users):
    with open(DATA_FILE, "w") as f:
        json.dump(users, f)

async def start(update, context):
    users = load_users()
    user_id = update.message.from_user.id

    if user_id not in users:
        users.append(user_id)
        save_users(users)

    await update.message.reply_text("✔ आप सफलतापूर्वक जुड़ गए!\nअब आपको सभी messages मिलेंगे।")

async def broadcast(update, context):
    if update.message.from_user.id != OWNER_ID:
        return

    users = load_users()

    for uid in users:
        try:
            await context.bot.copy_message(
                chat_id=uid,
                from_chat_id=update.message.chat_id,
                message_id=update.message.message_id
            )
        except:
            pass

    await update.message.reply_text("✔ Broadcast सभी users को भेज दिया गया!")

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.ALL, broadcast))

app.run_polling()
