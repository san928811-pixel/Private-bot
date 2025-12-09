# Final ready-to-paste bot code — includes unlock-button + start-only counting + clean links

import logging
import asyncio
from datetime import datetime, timedelta

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
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
TOKEN = "8541388990:AAEPBbQhA8jCxA4rlI71gOgOHUWuPS1jVJU"  # <-- replace if needed
MONGO_URI = "mongodb+srv://san928811_db_user:7OufFF7Ux8kOBnrO@cluster0.l1kszyc.mongodb.net/?appName=Cluster0"
ADMIN_IDS = {7895892794}  # <-- your admin id(s)
BOT_USERNAME = "Anjalipyarkiduniya_bot"  # <-- your bot username (without @)

BROADCAST_LIMIT = 10

# ================== DB ==================
client = MongoClient(MONGO_URI, server_api=ServerApi("1"))
db = client["anjali_bot"]
users_col = db["users"]
broadcasts_col = db["broadcasts"]

# ================== LOGGING ==================
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# ================== CONTENT ==================
WELCOME_TEXT = (
    "👋 *Welcome to Anjali Ki Duniya*\n\n"
    "🔥 यहाँ आपको Daily New Best Collection Videos मिलेंगी!\n"
    "👇 नीचे दिए गए channels join करें 👇\n"
)

CHANNEL_LINKS = [
    ("🔥 Open Video", "https://t.me/+sBJuAWxsHiIxY2E0"),
    ("💙 Instagram Collection", "https://t.me/+H_ExJVtnFuMxMzQ0"),
    ("⚡ All Viral Hub", "https://t.me/+oM9_I2afhqUzOTE0"),
    ("🎬 Full Open Video AB", "https://t.me/+4RLmy0Z3rCBhYWZk"),
]

# Unlock (small) message shown immediately after approve
UNLOCK_TEXT = (
    "🔓 *Unlock Access Required*\n\n"
    "👇 नीचे दिए गए *START* बटन को दबाए बिना आगे कुछ भी दिखाई नहीं देगा।\n"
    "➡️ कृपया तुरंत *START* दबाएँ!\n\n"
    "⭐ शुरू करने के लिए तीन जगह START दिखाया गया है ताकि आसानी से दिख जाए:\n"
    "1️⃣ START दबाएँ और आगे बढ़ें\n"
    "2️⃣ START without delay\n"
    "3️⃣ Please tap START to continue\n\n"
    "*English:*\n"
    "To unlock full access, press the *START NOW* button below 👇\n"
)

# ================== HELPERS ==================
def is_admin(uid: int) -> bool:
    return uid in ADMIN_IDS


def upsert_user(user):
    """Register user in DB — called ONLY when user presses /start."""
    if not user:
        return
    now = datetime.utcnow()
    users_col.update_one(
        {"user_id": user.id},
        {
            "$set": {
                "first_name": getattr(user, "first_name", ""),
                "username": getattr(user, "username", ""),
                "active": True,
                "last_active": now,
            },
            "$setOnInsert": {"joined_at": now},
        },
        upsert=True,
    )


def mark_inactive(uid: int):
    users_col.update_one({"user_id": uid}, {"$set": {"active": False}})


def get_active_users():
    return [doc["user_id"] for doc in users_col.find({"active": True}, {"user_id": 1})]


def count_active() -> int:
    return users_col.count_documents({"active": True})


def count_total() -> int:
    return users_col.count_documents({})


def count_today() -> int:
    today = datetime.utcnow().date()
    start = datetime(today.year, today.month, today.day)
    end = start + timedelta(days=1)
    return users_col.count_documents({"joined_at": {"$gte": start, "$lt": end}, "active": True})


# ================== MESSAGES BUILDERS ==================
def build_links_text() -> str:
    txt = "🔗 *Important Links*\n\n"
    for name, link in CHANNEL_LINKS:
        txt += f"• {name} – {link}\n"
    return txt


def build_start_keyboard():
    # deep-link so Telegram shows big blue START when user opens bot
    url = f"https://t.me/{BOT_USERNAME}?start=start"
    return InlineKeyboardMarkup([[InlineKeyboardButton("▶️ START NOW", url=url)]])


async def send_full_welcome(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    try:
        await context.bot.send_message(chat_id=chat_id, text=WELCOME_TEXT, parse_mode="Markdown")
        await context.bot.send_message(chat_id=chat_id, text=build_links_text(), parse_mode="Markdown")
    except Exception as e:
        log.warning("send_full_welcome failed for %s: %s", chat_id, e)


# ================== BROADCAST WORKER ==================
async def run_broadcast(context: ContextTypes.DEFAULT_TYPE, users: list, msgs: list, reply_msg):
    sent = 0
    failed = 0
    for uid in users:
        try:
            for m in msgs:
                # copy each message to user
                sent_msg = await m.copy(chat_id=uid)
                # store for delete later
                broadcasts_col.insert_one(
                    {"chat_id": uid, "message_id": sent_msg.message_id, "created_at": datetime.utcnow()}
                )
            sent += 1
        except Exception as e:
            failed += 1
            mark_inactive(uid)
            log.warning("broadcast to %s failed: %s", uid, e)
        await asyncio.sleep(0.05)
    await reply_msg.reply_text(f"📢 Broadcast Completed!\n✔ Sent: {sent}\n❌ Failed: {failed}")


# ================== HANDLERS ==================
async def join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Approve join request, DO NOT register in DB here.
    Send only small unlock message + START deep-link button.
    """
    req = update.chat_join_request
    user = req.from_user
    try:
        await req.approve()
        log.info("Approved join request for %s", user.id)
    except Exception as e:
        log.warning("approve failed %s: %s", getattr(user, "id", None), e)
        return

    # Send small unlock message with multiple START hints and a big clickable START NOW
    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=UNLOCK_TEXT,
            parse_mode="Markdown",
            reply_markup=build_start_keyboard(),
        )
        log.info("Sent unlock message to %s", user.id)
    except Exception as e:
        # If bot cannot DM (user blocked or privacy), ignore — user can still click bot link manually
        log.warning("Cannot send unlock DM to %s: %s", user.id, e)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User pressed /start — now register and send full welcome + links."""
    user = update.effective_user
    upsert_user(user)
    await send_full_welcome(user.id, context)


# Admin panel quick status (simple)
async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        return
    kb = ReplyKeyboardMarkup(
        [
            ["📊 Active Users", "📈 Today Joined"],
            ["👥 Total Users"],
            ["📢 Broadcast", "📤 Forward Broadcast"],
            ["🧹 Delete All", "❌ Cancel"],
        ],
        resize_keyboard=True,
    )
    await update.message.reply_text("🛠 *ADMIN PANEL*", parse_mode="Markdown", reply_markup=kb)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        return
    context.user_data.clear()
    await update.message.reply_text("❌ Broadcast Mode OFF")


async def delete_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        return
    deleted = 0
    bot = context.bot
    cursor = broadcasts_col.find({})
    for doc in cursor:
        try:
            await bot.delete_message(chat_id=doc.get("chat_id"), message_id=doc.get("message_id"))
            deleted += 1
        except Exception:
            pass
    broadcasts_col.delete_many({})
    await update.message.reply_text(f"🧹 Deleted: {deleted}")


async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Only admin messages are handled for panel/broadcast commands.
    Regular users: we do not auto-upsert here (only /start registers).
    """
    msg = update.message
    if not msg:
        return
    user = update.effective_user
    text = msg.text or ""

    # keep last_active only for registered users (if they exist)
    try:
        users_col.update_one({"user_id": user.id, "active": True}, {"$set": {"last_active": datetime.utcnow()}})
    except Exception:
        pass

    # Admin-only controls
    if not is_admin(user.id):
        return

    mode = context.user_data.get("mode")

    # Broadcast flow
    if mode == "broadcast":
        msgs = context.user_data.get("msgs", [])
        if text.lower() == "done":
            users = get_active_users()
            await msg.reply_text("📢 Broadcasting started…")
            asyncio.create_task(run_broadcast(context, users, msgs, msg))
            context.user_data.clear()
            return
        if len(msgs) < BROADCAST_LIMIT:
            msgs.append(msg)
            context.user_data["msgs"] = msgs
            await msg.reply_text(f"📩 Message saved ({len(msgs)})\nType DONE when finished.")
        else:
            await msg.reply_text("❗ Limit reached (10 messages). Type DONE to start broadcast.")
        return

    # Admin menu actions
    if text in ("📢 Broadcast", "📤 Forward Broadcast"):
        context.user_data["mode"] = "broadcast"
        context.user_data["msgs"] = []
        await msg.reply_text(
            "📢 Broadcast Mode ON\n🔹 Send messages/photos/videos to save\n🔹 Type DONE to start sending to all active users",
            reply_markup=ReplyKeyboardMarkup(
                [["❌ Cancel"]], resize_keyboard=True
            ),
        )
        return

    if text == "📊 Active Users":
        await msg.reply_text(f"👥 Active Users: {count_active()}")
    elif text == "📈 Today Joined":
        await msg.reply_text(f"📆 Today Joined: {count_today()}")
    elif text == "👥 Total Users":
        await msg.reply_text(f"📌 Total Users: {count_total()}")
    elif text == "🧹 Delete All":
        await delete_all(update, context)
    elif text == "❌ Cancel":
        await cancel(update, context)


# ================== START APP ==================
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(ChatJoinRequestHandler(join_request))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("panel", panel))
    app.add_handler(CommandHandler("cancel", cancel))

    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, text_router))

    print("BOT RUNNING…")
    app.run_polling()
