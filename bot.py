from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    Message
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from datetime import datetime

# ==============================
# BOT TOKEN
# ==============================
TOKEN = "7936792037:AAEY8w1SamKAanqZr66Lbfd_DKUK0GUzC18"

# ==============================
# ADMIN IDs
# ==============================
ADMINS = {7895892794}

# ==============================
# USER DATABASE
# ==============================
USERS = set()
TODAY = set()
ONLINE = set()

# message tracking for delete sync
LAST_BROADCAST = {}  # {user_id : message_id}


# ==============================
# /start
# ==============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    USERS.add(uid)
    TODAY.add(uid)
    ONLINE.add(uid)

    welcome = (
        "👋 *Welcome to Anjali Ki Duniya*\n\n"
        "⏳ जल्द ही आपको Best Collection Videos मिलना शुरू हो जाएँगी।"
    )

    await update.message.reply_text(welcome, parse_mode="Markdown")


# ==============================
# /id command
# ==============================
async def show_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text(f"🆔 Your ID: `{uid}`", parse_mode="Markdown")


# ==============================
# ADMIN PANEL
# ==============================
async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid not in ADMINS:
        return await update.message.reply_text("❌ You are not admin.")

    keyboard = [
        [InlineKeyboardButton("📊 Total Users", callback_data="total_users")],
        [InlineKeyboardButton("📅 Today Joined", callback_data="today_joined")],
        [InlineKeyboardButton("🟢 Online Users", callback_data="online_users")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast_mode")],
        [InlineKeyboardButton("❌ Delete All Broadcast", callback_data="delete_all")],
        [InlineKeyboardButton("📨 Forward Broadcast", callback_data="forward")],
        [InlineKeyboardButton("🚫 Auto Fake Report Block", callback_data="fake_block")],
        [InlineKeyboardButton("👑 Admin List", callback_data="admin_list")],
    ]

    await update.message.reply_text(
        "🛠 *ADMIN CONTROL PANEL*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


# ==============================
# BUTTON HANDLERS
# ==============================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    await q.answer()

    if uid not in ADMINS:
        return

    # --------------------------
    # Total Users
    # --------------------------
    if q.data == "total_users":
        await q.edit_message_text(f"📊 Total Users: {len(USERS)}")

    # --------------------------
    # Today Joined
    # --------------------------
    elif q.data == "today_joined":
        await q.edit_message_text(f"📅 Today Joined: {len(TODAY)}")

    # --------------------------
    # Online Users
    # --------------------------
    elif q.data == "online_users":
        await q.edit_message_text(f"🟢 Online Users: {len(ONLINE)}")

    # --------------------------
    # Broadcast Mode ON
    # --------------------------
    elif q.data == "broadcast_mode":
        context.user_data["broadcast"] = True
        await q.edit_message_text(
            "📢 *Broadcast Mode ON*\nअब कोई भी message reply/forward करके भेजें → सभी users को पहुँचेगा।",
            parse_mode="Markdown"
        )

    # --------------------------
    # Forward mode
    # --------------------------
    elif q.data == "forward":
        context.user_data["fwd"] = True
        await q.edit_message_text(
            "📨 Forward Mode ON\nForward किया हुआ message सबको भेजा जाएगा।",
            parse_mode="Markdown"
        )

    # --------------------------
    # Delete All Broadcast
    # --------------------------
    elif q.data == "delete_all":
        deleted = 0
        for user, msg_id in LAST_BROADCAST.items():
            try:
                await context.bot.delete_message(chat_id=user, message_id=msg_id)
                deleted += 1
            except:
                pass

        LAST_BROADCAST.clear()

        await q.edit_message_text(f"❌ Deleted Broadcast Messages from {deleted} users.")

    # --------------------------
    # Show admin list
    # --------------------------
    elif q.data == "admin_list":
        await q.edit_message_text(f"👑 Admins:\n{ADMINS}")

    # --------------------------
    # fake report mode
    # --------------------------
    elif q.data == "fake_block":
        context.user_data["fake"] = True
        await q.edit_message_text("🚫 Reply to user ID to remove.")


# ==============================
# BROADCAST HANDLER
# ==============================
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    # --------------------------
    # Broadcast Mode
    # --------------------------
    if uid in ADMINS and context.user_data.get("broadcast"):

        # send to everyone & save msg_id
        for user in USERS:
            try:
                sent_msg = await update.message.copy(chat_id=user)
                LAST_BROADCAST[user] = sent_msg.message_id
            except:
                pass

        context.user_data["broadcast"] = False
        await update.message.reply_text("📢 Broadcast Sent Successfully!")
        return

    # --------------------------
    # Forward Mode
    # --------------------------
    if uid in ADMINS and context.user_data.get("fwd"):

        for user in USERS:
            try:
                sent_msg = await update.message.forward(chat_id=user)
                LAST_BROADCAST[user] = sent_msg.message_id
            except:
                pass

        context.user_data["fwd"] = False
        await update.message.reply_text("📨 Forward Broadcast Sent!")
        return


# ==============================
# MAIN
# ==============================
def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("id", show_id))
    app.add_handler(CommandHandler("panel", panel))

    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, message_handler))

    app.run_polling()


if __name__ == "__main__":
    main()
