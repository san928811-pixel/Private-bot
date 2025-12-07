import logging
from datetime import datetime, timedelta

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ChatJoinRequestHandler,
)

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# ================== CONFIG ==================
TOKEN = "8541388990:AAEPBbQhA8jCxA4rlI71gOgOHUWuPS1jVJU"
MONGO_URI = MONGO_URI = "mongodb+srv://san928811_db_user:7OufFF7Ux8kOBnrO@cluster0.l1kszyc.mongodb.net/?appName=Cluster0"
ADMIN_IDS = ADMIN_IDS = {7895892794}

# Welcome text and links
WELCOME_TEXT = (
    "👋 *Welcome to Anjali Ki Duniya*\n\n"
    "⏳  जल्द ही आपको यहाँ Best Collection Videos के अपडेट मिलना शुरू हो जाएँगे।"
)

WELCOME_LINKS = [
    "[🔥 Open Video](https://t.me/+sBJuAWxsHiIxY2E0)",
    "[💙 Instagram Collection](https://t.me/+H_ExJVtnFuMxMzQ0)",
    "[⚡ All Viral Hub](https://t.me/+oM9_I2afhqUzOTE0)",
    "[🎬 Full Open Video AB](https://t.me/+4RLmy0Z3rCBhYWZk)"
]

# ================== DB SETUP ==================

client = MongoClient(MONGO_URI, server_api=ServerApi("1"))
db = client["anjali_bot"]
users_col = db["users"]
broadcasts_col = db["broadcasts"]

# ================== LOGGING ==================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
log = logging.getLogger(__name__)

# ================== HELPERS ==================


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def upsert_user(telegram_user) -> None:
    if telegram_user is None:
        return
    uid = telegram_user.id
    first_name = telegram_user.first_name or ""
    username = telegram_user.username or ""
    now = datetime.utcnow()

    existing = users_col.find_one({"user_id": uid})
    if existing:
        users_col.update_one(
            {"user_id": uid},
            {
                "$set": {
                    "first_name": first_name,
                    "username": username,
                    "last_active_at": now,
                    "active": True,
                }
            },
        )
    else:
        users_col.insert_one(
            {
                "user_id": uid,
                "first_name": first_name,
                "username": username,
                "joined_at": now,
                "last_active_at": now,
                "banned": False,
                "active": True,
            }
        )


def mark_inactive(user_id: int) -> None:
    users_col.update_one(
        {"user_id": user_id},
        {"$set": {"active": False}},
        upsert=True,
    )


def ban_user(user_id: int) -> None:
    users_col.update_one(
        {"user_id": user_id},
        {"$set": {"banned": True, "banned_at": datetime.utcnow(), "active": False}},
        upsert=True,
    )


def get_all_active_users():
    cursor = users_col.find(
        {"banned": {"$ne": True}, "active": True},
        {"user_id": 1},
    )
    return [doc["user_id"] for doc in cursor]


def count_total_users() -> int:
    return users_col.count_documents({"banned": {"$ne": True}, "active": True})


def count_today_users() -> int:
    today = datetime.utcnow().date()
    start = datetime(today.year, today.month, today.day)
    end = start + timedelta(days=1)
    return users_col.count_documents(
        {
            "joined_at": {"$gte": start, "$lt": end},
            "banned": {"$ne": True},
            "active": True,
        }
    )

admin_keyboard = ReplyKeyboardMarkup(
    [
        ["📊 Total Users", "📈 Today Joined"],
        ["📢 Broadcast", "📤 Forward Broadcast"],
        ["❌ Delete All Broadcast"],
    ],
    resize_keyboard=True,
)


async def send_welcome_with_links(update_or_chat, context: ContextTypes.DEFAULT_TYPE = None):
    try:
        if isinstance(update_or_chat, Update):
            chat = update_or_chat.effective_chat
            await chat.send_message(WELCOME_TEXT, parse_mode="Markdown")
            links_text = "🔗 *Important Links:*\n" + "\n".join(f"• {link}" for link in WELCOME_LINKS)
            await chat.send_message(links_text, parse_mode="Markdown")
        else:
            chat_id = int(update_or_chat)
            bot = context.bot if context else None
            if bot:
                await bot.send_message(chat_id=chat_id, text=WELCOME_TEXT, parse_mode="Markdown")
                links_text = "🔗 *Important Links:*\n" + "\n".join(f"• {link}" for link in WELCOME_LINKS)
                await bot.send_message(chat_id=chat_id, text=links_text, parse_mode="Markdown")
    except Exception as e:
        log.warning(f"Failed to send welcome/links: {e}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    upsert_user(user)

    await update.message.reply_text(
        WELCOME_TEXT,
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    links_text = "🔗 *Important Links:*\n" + "\n".join(f"• {link}" for link in WELCOME_LINKS)
    await update.message.reply_text(links_text, parse_mode="Markdown")


async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(f"🆔 Your Telegram ID: `{user.id}`", parse_mode="Markdown")


async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        return
    await update.message.reply_text("🛠 *ADMIN PANEL*", parse_mode="Markdown", reply_markup=admin_keyboard)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        return
    context.user_data.pop("mode", None)
    await update.message.reply_text("❌ Broadcast mode band ho gaya.", reply_markup=admin_keyboard)


async def delete_all_broadcasts(context: ContextTypes.DEFAULT_TYPE) -> int:
    deleted = 0
    cursor = broadcasts_col.find({})
    for doc in cursor:
        chat_id = doc.get("chat_id")
        msg_id = doc.get("message_id")
        if not chat_id or not msg_id:
            continue
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except:
            pass
    broadcasts_col.delete_many({})
    return deleted


async def do_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_msg = update.message
    user_ids = get_all_active_users()

    success = 0
    fail = 0

    for uid in user_ids:
        try:
            sent = await admin_msg.copy(chat_id=uid)
            broadcasts_col.insert_one(
                {"chat_id": uid, "message_id": sent.message_id, "created_at": datetime.utcnow()}
            )
            success += 1
        except Exception as e:
            fail += 1
            mark_inactive(uid)
            log.warning(f"Broadcast fail to {uid}: {e}")

    await admin_msg.reply_text(
        f"📢 Broadcast done.\n✅ Success: {success}\n❌ Fail: {fail}",
        reply_markup=admin_keyboard,
    )


async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if msg is None:
        return

    user = update.effective_user
    text = msg.text or ""
    upsert_user(user)

    if not is_admin(user.id):
        lower = text.lower()
        bad_words = ["spam", "fake", "fraud", "scam", "report", "fake bot", "scam bot"]
        if any(word in lower for word in bad_words):
            ban_user(user.id)
            try:
                await msg.reply_text("🚫 Suspicious activity, you are banned.")
            except:
                pass
        return

    mode = context.user_data.get("mode")
    if mode == "broadcast":
        await do_broadcast(update, context)
        return

    if text == "📊 Total Users":
        total = count_total_users()
        await msg.reply_text(f"📊 Total Active Users: *{total}*", parse_mode="Markdown")

    elif text == "📈 Today Joined":
        today_count = count_today_users()
        await msg.reply_text(f"📈 आज join किए active users: *{today_count}*", parse_mode="Markdown")

    elif text in ("📢 Broadcast", "📤 Forward Broadcast"):
        context.user_data["mode"] = "broadcast"
        await msg.reply_text(
            "📢 *Broadcast Mode ON*\n\n"
            "🔹 Ab jitne bhi *messages / photos / videos / albums* bhejोगे,\n"
            "🔹 Sab active users tak पहुंचेंगे।\n\n"
            "❌ बंद करने के लिए /cancel भेजो।",
            parse_mode="Markdown",
            reply_markup=admin_keyboard,
        )

    elif text == "❌ Delete All Broadcast":
        deleted = await delete_all_broadcasts(context)
        await msg.reply_text(
            f"🧹 Deleted broadcast messages: {deleted}",
            reply_markup=admin_keyboard,
        )

    else:
        log.info("Admin %s sent: %s", user.id, text)


async def join_request_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    req = update.chat_join_request
    user = req.from_user
    upsert_user(user)
    try:
        await req.approve()
    except Exception as e:
        log.warning(f"Join request approve fail for {user.id}: {e}")
        return

    # DM me welcome + links
    try:
        await send_welcome_with_links(user.id, context)
    except Exception as e:
        log.warning(f"Failed to send welcome after join approve: {e}")


if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("panel", panel))
    app.add_handler(CommandHandler("id", get_id))
    app.add_handler(CommandHandler("cancel", cancel))

    app.add_handler(ChatJoinRequestHandler(join_request_handler))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, text_router))

    print("Bot Running...")
    app.run_polling()
