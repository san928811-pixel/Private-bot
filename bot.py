import json
import os
from datetime import date
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ===============================
# CONFIGURATION
# ===============================

TOKEN = "7936792037:AAEY8w1SamKAanqZr66Lbfd_DKUK0GUzC18"

# 👉 MULTIPLE ADMINS
ADMIN_IDS = [
    7895892794,   # आपका ID (Main Admin)
    123456789,    # दूसरा admin ID (replace)
    987654321     # तीसरा admin ID (replace)
]

USERS_FILE = "users.json"


# ===============================
# USER STORAGE
# ===============================

def load_users():
    if not os.path.exists(USERS_FILE):
        return []

    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return []


def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)


def add_user(user_id: int):
    users = load_users()
    today = date.today().isoformat()

    for u in users:
        if u["id"] == user_id:
            return

    users.append({"id": user_id, "date": today})
    save_users(users)


def remove_user(user_id: int):
    users = load_users()
    users = [u for u in users if u["id"] != user_id]
    save_users(users)


# ===============================
# AUTO REMOVE SUSPICIOUS USERS
# ===============================

def is_suspicious(user):
    """अगर user की profile अधूरी है या suspicious है तो True return करो"""

    if not user.first_name:
        return True

    if user.is_bot:
        return True

    # No username + no last name = suspicious
    if not user.username and not user.last_name:
        return True

    return False


# ===============================
# START → WELCOME + AUTO-REMOVE
# ===============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # Remove suspicious users automatically
    if is_suspicious(user):
        remove_user(user.id)
        await update.message.reply_text("⚠️ आपकी profile complete नहीं है, इसलिए access block किया गया है।")
        return

    add_user(user.id)

    welcome_text = (
        "👋 Welcome to *Anjali Ki Duniya*\n\n"
        "⏳ आपको थोड़ी देर बाद यहाँ Best Collection Videos के अपडेट मिलने शुरू हो जाएंगे।"
    )

    await update.message.reply_markdown(welcome_text)


# ===============================
# ADMIN ONLY COMMANDS
# ===============================

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in ADMIN_IDS:
        return

    users = load_users()
    total = len(users)
    today = date.today().isoformat()

    today_joined = len([u for u in users if u["date"] == today])
    online = max(1, total // 10)

    msg = (
        "📊 *Anjali Ki Duniya – Bot Stats*\n\n"
        f"👥 Total Users: *{total}*\n"
        f"📅 Today Joined: *{today_joined}*\n"
        f"🟢 Approx Online: *{online}*"
    )

    await update.message.reply_markdown(msg)


async def today_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in ADMIN_IDS:
        return

    users = load_users()
    today = date.today().isoformat()

    today_users = [u["id"] for u in users if u["date"] == today]

    if not today_users:
        await update.message.reply_text("📅 आज कोई नया user नहीं जुड़ा।")
        return

    msg = "📅 *Today Joined Users:*\n\n"
    for u in today_users:
        msg += f"• `{u}`\n"

    await update.message.reply_markdown(msg)


async def all_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in ADMIN_IDS:
        return

    users = load_users()
    msg = "📋 *All Users List:*\n\n"

    for u in users:
        msg += f"• `{u['id']}` — Joined: *{u['date']}*\n"

    await update.message.reply_markdown(msg)


# ===============================
# BROADCAST SYSTEM
# ===============================

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in ADMIN_IDS:
        return

    users = load_users()
    sent = 0
    failed = 0

    # Media Broadcast (reply to message)
    if update.message.reply_to_message:
        src = update.message.reply_to_message
        for u in users:
            try:
                await context.bot.copy_message(
                    chat_id=u["id"],
                    from_chat_id=src.chat_id,
                    message_id=src.message_id,
                )
                sent += 1
            except:
                failed += 1

        await update.message.reply_text(f"📢 Media Broadcast\nSent: {sent}\nFailed: {failed}")
        return

    # Text Broadcast
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("❗ Broadcast use: /broadcast your message")
        return

    for u in users:
        try:
            await context.bot.send_message(chat_id=u["id"], text=text)
            sent += 1
        except:
            failed += 1

    await update.message.reply_text(f"📢 Text Broadcast\nSent: {sent}\nFailed: {failed}")


# ===============================
# BLOCK ALL USER MESSAGES
# ===============================

async def block_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id

    if uid in ADMIN_IDS:
        return

    try:
        await update.message.delete()
    except:
        pass


# ===============================
# MAIN
# ===============================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("todaylist", today_list))
    app.add_handler(CommandHandler("allusers", all_users))
    app.add_handler(CommandHandler("broadcast", broadcast))

    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, block_messages))

    app.run_polling()


if __name__ == "__main__":
    main()
