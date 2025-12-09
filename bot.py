# ================== IMPORTS ==================
import logging
import asyncio
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
TOKEN = "8541388990:AAEPBbQhA8jCxA4rlI71gOgOHUWuPS1jVJU"  # <-- yahan apna token daalo
MONGO_URI = "mongodb+srv://san928811_db_user:7OufFF7Ux8kOBnrO@cluster0.l1kszyc.mongodb.net/?appName=Cluster0"  # <-- yahan apna Mongo URI daalo
ADMIN_IDS = {7895892794}  # <-- apna admin id

# Bot username (used to create start-link that shows big blue START button)
BOT_USERNAME = "Anjalipyarkiduniya_bot"  # <-- tumhara bot username

# Short instruction (first message) will be bilingual and force user to click the t.me start link
UNLOCK_TEXT_HINDI_EN = (
    "👋 *Welcome! / स्वागत हैं!*\n\n"
    "🔒 हिंदी:\n"
    "पूरा welcome message देखने और access पाने के लिए नीचे START दबाएँ (या link पर क्लिक करें)।\n\n"
    "🔒 English:\n"
    "To unlock the full welcome message and access, please press START below (or click the link).\n\n"
    "👉 Click this link to open bot and see START button:\n"
    f"https://t.me/{BOT_USERNAME}?start=start\n\n"
    "🔔 After pressing START, you will receive the full welcome message and links."
)

# This is the full welcome (sent only after /start). We'll include Hindi + English + Name - Link format.
WELCOME_TITLE = "👋 Welcome to Anjali Ki Duniya / Anjali’s World\n\n"

CHANNEL_LINKS = [
    ("🔥 Open Video", "https://t.me/+sBJuAWxsHiIxY2E0"),
    ("💙 Instagram Collection", "https://t.me/+H_ExJVtnFuMxMzQ0"),
    ("⚡ All Viral Hub", "https://t.me/+oM9_I2afhqUzOTE0"),
    ("🎬 Full Open Video AB", "https://t.me/+4RLmy0Z3rCBhYWZk"),
]

BROADCAST_LIMIT = 10

# ================== DB ==================
client = MongoClient(MONGO_URI, server_api=ServerApi("1"))
db = client["anjali_bot"]
users_col = db["users"]
broadcasts_col = db["broadcasts"]

# ================== LOGGING ==================
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# ================== HELPERS ==================
def is_admin(uid: int) -> bool:
    return uid in ADMIN_IDS


def upsert_user(u):
    """Only called when user presses /start — that makes them counted/active."""
    if not u:
        return
    users_col.update_one(
        {"user_id": u.id},
        {
            "$set": {
                "first_name": u.first_name,
                "username": u.username,
                "active": True,
                "last_active": datetime.utcnow(),
            },
            "$setOnInsert": {"joined_at": datetime.utcnow()},
        },
        upsert=True,
    )


def mark_inactive(uid: int):
    users_col.update_one({"user_id": uid}, {"$set": {"active": False}})


def get_active_users():
    return [u["user_id"] for u in users_col.find({"active": True})]


def count_active() -> int:
    return users_col.count_documents({"active": True})


def count_total() -> int:
    return users_col.count_documents({})


def count_today() -> int:
    today = datetime.utcnow().date()
    start = datetime(today.year, today.month, today.day)
    end = start + timedelta(days=1)
    return users_col.count_documents(
        {"joined_at": {"$gte": start, "$lt": end}, "active": True}
    )


# ================== WELCOME / LINKS BUILDERS ==================
def build_links_text() -> str:
    # Name – Link format, no inline buttons
    t = "🔗 Important Links / महत्वपूर्ण लिंक्स:\n\n"
    for name, link in CHANNEL_LINKS:
        t += f"👉 {name} – {link}\n"
    return t


async def send_full_welcome(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Send the full bilingual welcome + links (called after /start)."""
    try:
        # bilingual intro
        intro = (
            "🎉 *Welcome to Anjali Ki Duniya* 🎉\n\n"
            "🇮🇳 (Hindi)\n"
            "आपका स्वागत है! अब आप यहाँ सभी Premium Videos, Viral Content और Daily Updates देख पाएंगे।\n\n"
            "🇬🇧 (English)\n"
            "Welcome! You can now access all premium videos, viral content, and daily updates.\n\n"
        )
        await context.bot.send_message(chat_id, intro, parse_mode="Markdown")
        # links in Name – Link format
        links_text = build_links_text()
        await context.bot.send_message(chat_id, links_text)
    except Exception as e:
        log.warning(f"Full welcome send failed to {chat_id}: {e}")


async def send_unlock_message(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Send the initial bilingual unlock message instructing user to press START."""
    try:
        await context.bot.send_message(chat_id, UNLOCK_TEXT_HINDI_EN, parse_mode="Markdown")
    except Exception as e:
        log.warning(f"Unlock message failed to {chat_id}: {e}")


# ================== BACKGROUND BROADCAST ==================
async def run_broadcast(
    context: ContextTypes.DEFAULT_TYPE,
    users: list[int],
    msgs: list,
    reply_msg,
):
    sent = 0
    fail = 0

    for uid in users:
        try:
            for m in msgs:
                sent_msg = await m.copy(chat_id=uid)
                # store for Delete All
                broadcasts_col.insert_one(
                    {
                        "chat_id": uid,
                        "message_id": sent_msg.message_id,
                        "created_at": datetime.utcnow(),
                    }
                )
            sent += 1
        except Exception as e:
            fail += 1
            mark_inactive(uid)
            log.warning(f"Broadcast failed for {uid}: {e}")

        await asyncio.sleep(0.05)

    await reply_msg.reply_text(
        f"📢 Broadcast Completed!\n✔ Sent: {sent}\n❌ Failed: {fail}"
    )


# ================== ADMIN KEYBOARD ==================
admin_keyboard = ReplyKeyboardMarkup(
    [
        ["📊 Active Users", "📈 Today Joined"],
        ["👥 Total Users"],
        ["📢 Broadcast", "📤 Forward Broadcast"],
        ["🧹 Delete All", "❌ Cancel"],
    ],
    resize_keyboard=True,
)

# ================== COMMANDS ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    User pressed /start — this is the ONLY action that registers them as a member.
    After this we'll send the full welcome + links.
    """
    user = update.effective_user
    upsert_user(user)  # only now we save them (count + broadcast target)
    cid = user.id
    await send_full_welcome(cid, context)


async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text(
        "🛠 *ADMIN PANEL*", parse_mode="Markdown", reply_markup=admin_keyboard
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    context.user_data.clear()
    await update.message.reply_text(
        "❌ Broadcast Mode OFF", reply_markup=admin_keyboard
    )


# ================== JOIN REQUEST HANDLER ==================
async def join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    When someone requests to join the channel/group:
    - Approve the request
    - DO NOT register them in DB
    - Send only the bilingual unlock message that instructs them to press START
    """
    req = update.chat_join_request
    u = req.from_user

    try:
        await req.approve()
    except Exception as e:
        log.warning(f"Join approve failed for {u.id}: {e}")
        return

    # Do NOT upsert_user(u) here — we only register on /start
    await send_unlock_message(u.id, context)


# ================== ADMIN ACTIONS ==================
async def delete_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    deleted = 0
    cursor = broadcasts_col.find({})
    async_bot = context.bot

    for doc in cursor:
        chat_id = doc.get("chat_id")
        msg_id = doc.get("message_id")
        if not chat_id or not msg_id:
            continue
        try:
            await async_bot.delete_message(chat_id=chat_id, message_id=msg_id)
            deleted += 1
        except Exception as e:
            log.warning(f"Delete failed: {e}")

    broadcasts_col.delete_many({})
    await update.message.reply_text(
        f"🧹 Deleted: {deleted}", reply_markup=admin_keyboard
    )


# ================== MAIN TEXT ROUTER ==================
async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    user = update.effective_user
    text = msg.text or ""

    # Note: we do NOT upsert on random messages — only on /start
    # But keep last_active for users who are already registered
    try:
        users_col.update_one(
            {"user_id": user.id, "active": True},
            {"$set": {"last_active": datetime.utcnow()}},
        )
    except Exception:
        pass

    # --------- Non-admin ignore (admin-only commands) ---------
    if not is_admin(user.id):
        return

    # --------- Broadcast Mode ---------
    mode = context.user_data.get("mode")
    if mode == "broadcast":
        msgs = context.user_data["msgs"]

        if text.lower() == "done":
            users = get_active_users()
            await msg.reply_text("📢 Broadcasting started…")

            asyncio.create_task(run_broadcast(context, users, msgs, msg))

            context.user_data.clear()
            return

        if len(msgs) < BROADCAST_LIMIT:
            msgs.append(msg)
            await msg.reply_text(
                f"📩 Message saved ({len(msgs)})\nType DONE when finished."
            )
        else:
            await msg.reply_text(
                "❗ Limit reached (10 messages). Type DONE to start broadcast."
            )
        return

    # --------- Admin Menu ---------
    if text in ("📢 Broadcast", "📤 Forward Broadcast"):
        context.user_data["mode"] = "broadcast"
        context.user_data["msgs"] = []
        await msg.reply_text(
            "📢 Broadcast Mode ON\n"
            "🔹 Ab jitne bhi messages / photos / videos bhejoge\n"
            "🔹 Sab active users ko jayenge.\n\n"
            "✅ Jab complete ho jaye to `DONE` type karo.",
            parse_mode="Markdown",
            reply_markup=admin_keyboard,
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


# ================== RUN BOT ==================
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("panel", panel))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(ChatJoinRequestHandler(join_request))

    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, text_router))

    print("BOT RUNNING…")
    app.run_polling()
