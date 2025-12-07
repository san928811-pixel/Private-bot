import json
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

TOKEN = "7936792037:AAEY8w1SamKAanqZr66Lbfd_DKUK0GUzC18"

# ==============================
# ADMIN LIST
# ==============================
ADMINS = {7895892794}

# ==============================
# LOAD USERS FROM FILE
# ==============================
def load_users():
    try:
        with open("users.json", "r") as f:
            return set(json.load(f))
    except:
        return set()

def save_users():
    with open("users.json", "w") as f:
        json.dump(list(USERS), f)

USERS = load_users()
LAST_BROADCAST = {}  # {user_id: message_id}


# ==============================
# START COMMAND
# ==============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    USERS.add(uid)
    save_users()

    welcome = (
        "👋 *Welcome to Anjali Ki Duniya*\n\n"
        "⏳ जल्द ही आपको यहाँ Best Collection Videos मिलना शुरू हो जाएँगी।"
    )

    await update.message.reply_text(welcome, parse_mode="Markdown")


# ==============================
# ID SHOW
# ==============================
async def show_id(update, context):
    uid = update.effective_user.id
    await update.message.reply_text(f"🆔 Your ID: `{uid}`", parse_mode="Markdown")


# ==============================
# ADMIN PANEL
# ==============================
async def panel(update, context):
    uid = update.effective_user.id
    if uid not in ADMINS:
        return await update.message.reply_text("❌ You are not admin.")

    keyboard = [
        [InlineKeyboardButton("📊 Total Users", callback_data="total")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")],
        [InlineKeyboardButton("❌ Delete All Broadcast", callback_data="delete")],
        [InlineKeyboardButton("📨 Forward Broadcast", callback_data="forward")],
    ]

    await update.message.reply_text(
        "🛠 *ADMIN PANEL*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


# ==============================
# BUTTON HANDLER
# ==============================
async def button_handler(update, context):
    q = update.callback_query
    uid = q.from_user.id
    await q.answer()

    if uid not in ADMINS:
        return

    # Show total users
    if q.data == "total":
        return await q.edit_message_text(f"📊 Total Users: {len(USERS)}")

    # Broadcast mode ON
    if q.data == "broadcast":
        context.user_data["broadcast"] = True
        return await q.edit_message_text("📢 Broadcast Mode ON — अब message भेजें।")

    # Forward broadcast mode
    if q.data == "forward":
        context.user_data["forward"] = True
        return await q.edit_message_text("📨 Forward Mode ON — Forward किया हुआ message सबको जाएगा।")

    # Delete all broadcast
    if q.data == "delete":
        deleted = 0
        for user, msg_id in LAST_BROADCAST.items():
            try:
                await context.bot.delete_message(chat_id=user, message_id=msg_id)
                deleted += 1
            except:
                pass

        LAST_BROADCAST.clear()
        return await q.edit_message_text(f"❌ Deleted {deleted} broadcast messages.")


# ==============================
# MESSAGE HANDLER
# ==============================
async def msg_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    # ---------- Broadcast System ----------
    if uid in ADMINS and context.user_data.get("broadcast"):

        # Message goes to all users
        for user in USERS:
            try:
                sent = await update.message.copy(chat_id=user)
                LAST_BROADCAST[user] = sent.message_id
            except:
                pass

        context.user_data["broadcast"] = False
        return await update.message.reply_text("📢 Broadcast Sent!")

    # ---------- Forward System ----------
    if uid in ADMINS and context.user_data.get("forward"):

        for user in USERS:
            try:
                sent = await update.message.forward(chat_id=user)
                LAST_BROADCAST[user] = sent.message_id
            except:
                pass

        context.user_data["forward"] = False
        return await update.message.reply_text("📨 Forward Broadcast Sent!")


# ==============================
# MAIN
# ==============================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("id", show_id))
    app.add_handler(CommandHandler("panel", panel))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, msg_handler))

    app.run_polling()


if __name__ == "__main__":
    main()
