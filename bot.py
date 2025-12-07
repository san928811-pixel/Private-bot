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
)

# ================== CONFIG ==================

TOKEN = "7936792037:AAEY8w1SamKAanqZr66Lbfd_DKUK0GUzC18"

# MongoDB connection string (jo tumne diya)
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

MONGO_URI = (
    "mongodb+srv://san928811_db_user:7OufFF7Ux8kOBnrO"
    "@cluster0.l1kszyc.mongodb.net/?appName=Cluster0"
)

client = MongoClient(MONGO_URI, server_api=ServerApi("1"))
db = client["anjali_bot"]
users_col = db["users"]
broadcasts_col = db["broadcasts"]

# Sirf ye log admin hain (tumhara ID)
ADMIN_IDS = {7895892794}

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
    """User ko MongoDB me save / update kare."""
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
            }
        )


def get_all_active_users():
    """Jo banned nahi hain, un sab users ki list."""
    cursor = users_col.find({"banned": {"$ne": True}}, {"user_id": 1})
    return [doc["user_id"] for doc in cursor]


def ban_user(user_id: int) -> None:
    users_col.update_one(
        {"user_id": user_id},
        {"$set": {"banned": True, "banned_at": datetime.utcnow()}},
        upsert=True,
    )


def count_total_users() -> int:
    return users_col.count_documents({"banned": {"$ne": True}})


def count_today_users() -> int:
    today = datetime.utcnow().date()
    start = datetime(today.year, today.month, today.day)
    end = start + timedelta(days=1)
    return users_col.count_documents(
        {"joined_at": {"$gte": start, "$lt": end}, "banned": {"$ne": True}}
    )


# ================== KEYBOARDS ==================

admin_keyboard = ReplyKeyboardMarkup(
    [
        ["📊 Total Users", "📈 Today Joined"],
        ["📢 Broadcast", "📤 Forward Broadcast"],
        ["❌ Delete All Broadcast"],
    ],
    resize_keyboard=True,
)

# ================== HANDLERS ==================


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    upsert_user(user)

    # Normal users ko sirf welcome message
    text = (
        "👋 *Welcome to Anjali Ki Duniya*\n\n"
        "⏳  जल्द ही आपको यहाँ Best Collection Videos के अपडेट मिलना शुरू हो जाएँगे।"
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )


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
    await update.message.reply_text("❌ Mode cancel ho gaya.", reply_markup=admin_keyboard)


async def delete_all_broadcasts(context: ContextTypes.DEFAULT_TYPE) -> int:
    """MongoDB se sare broadcast messages delete kare (jitna possible ho)."""
    deleted = 0
    cursor = broadcasts_col.find({})
    async for_doc = False  # just to keep python happy (not used)

    for doc in cursor:
        chat_id = doc.get("chat_id")
        msg_id = doc.get("message_id")
        if not chat_id or not msg_id:
            continue
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
            deleted += 1
        except Exception as e:
            # Ho sakta hai user ne chat delete kar di ho ya bot ke pass rights na ho
            log.warning("Delete failed for %s: %s", chat_id, e)

    broadcasts_col.delete_many({})
    return deleted


async def do_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin ka jo message aaya hai, use sab users ko copy kare."""
    admin_msg = update.message
    user_ids = get_all_active_users()

    success = 0
    fail = 0

    for uid in user_ids:
        try:
            # admin wale message ko as copy bhej rahe (text/photo/video sab chalega)
            sent = await admin_msg.copy(chat_id=uid)
            broadcasts_col.insert_one(
                {
                    "chat_id": uid,
                    "message_id": sent.message_id,
                    "created_at": datetime.utcnow(),
                }
            )
            success += 1
        except Exception as e:
            log.warning("Broadcast fail to %s: %s", uid, e)
            fail += 1

    await admin_msg.reply_text(
        f"📢 Broadcast done.\n✅ Success: {success}\n❌ Fail: {fail}",
        reply_markup=admin_keyboard,
    )


async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sab normal messages yahan aayenge (commands ke alawa)."""
    msg = update.message
    if msg is None:
        return

    user = update.effective_user
    text = msg.text or ""
    upsert_user(user)

    # ---------- Non-admin users ----------
    if not is_admin(user.id):
        lower = text.lower()

        # Fake / spam words detect karo, turant ban
        bad_words = ["spam", "fake", "fraud", "scam", "report", "fake bot", "scam bot"]
        if any(word in lower for word in bad_words):
            ban_user(user.id)
            try:
                await msg.reply_text(
                    "🚫 Aapko suspicious report/fake message ke karan bot se hata diya gaya hai."
                )
            except Exception:
                pass
        # Normal user ke message ka reply nahi dena
        return

    # ---------- Admin logic ----------
    mode = context.user_data.get("mode")

    # Agar abhi broadcast mode ON hai, to jo bhi message aya use sabko bhej do
    if mode == "broadcast":
        context.user_data.pop("mode", None)
        await do_broadcast(update, context)
        return

    # Agar koi mode nahi to buttons check karo
    if text == "📊 Total Users":
        total = count_total_users()
        await msg.reply_text(f"📊 Total Users: *{total}*", parse_mode="Markdown")

    elif text == "📈 Today Joined":
        today = count_today_users()
        await msg.reply_text(f"📈 Aaj join kiye: *{today}*", parse_mode="Markdown")

    elif text in ("📢 Broadcast", "📤 Forward Broadcast"):
        context.user_data["mode"] = "broadcast"
        await msg.reply_text(
            "📢 Jo message sab users ko bhejna hai, ab yahan send / forward karo.\n"
            "✅ Text, photo, video sab chalega.\n\n"
            "❌ Cancel karne ke liye /cancel bhejo.",
            reply_markup=admin_keyboard,
        )

    elif text == "❌ Delete All Broadcast":
        deleted = await delete_all_broadcasts(context)
        await msg.reply_text(
            f"❌ Delete All Broadcast complete.\n🧹 Deleted messages (approx): {deleted}",
            reply_markup=admin_keyboard,
        )

    else:
        # Admin ne normally chat kiya ho to ignore (ya log debug ke liye)
        log.info("Admin %s sent: %s", user.id, text)


# ================== MAIN ==================


async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("panel", panel))
    app.add_handler(CommandHandler("id", get_id))
    app.add_handler(CommandHandler("cancel", cancel))

    # Baaki sab messages
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, text_router))

    log.info("Bot starting...")
    await app.run_polling()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
