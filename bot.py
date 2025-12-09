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
TOKEN = "8541388990:AAEPBbQhA8jCxA4rlI71gOgOHUWuPS1jVJU"
MONGO_URI = "mongodb+srv://san928811_db_user:7OufFF7Ux8kOBnrO@cluster0.l1kszyc.mongodb.net/?appName=Cluster0"
ADMIN_IDS = {7895892794}

# ------------- SMALL UNLOCK MESSAGE (Sent immediately after join approve) -------------
UNLOCK_TEXT_HINDI_EN = (
    "🔓 *Unlock Access Required*\n\n"
    "👇 नीचे दिए गए Start बटन को दबाए बिना आगे कुछ नहीं दिखेगा।\n"
    "▶️ कृपया तुरंत *START* दबाएँ!\n\n"
    "**English:**\n"
    "To unlock full access, press the *START* button below.\n"
    "Tap START to continue 👇"
)

# ------------- MAIN WELCOME MESSAGE AFTER START -------------
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
    """START दबाने पर ही user active + joined माना जाएगा"""
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

# ================== WELCOME MESSAGE ==================
def build_links_text() -> str:
    t = "🔗 *Important Links*\n\n"
    for name, link in CHANNEL_LINKS:
        t += f"• [{name}]({link})\n"
    return t


async def send_full_welcome(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    """START दबाने के बाद वाला असली welcome"""
    try:
        await context.bot.send_message(chat_id, WELCOME_TEXT, parse_mode="Markdown")
        await context.bot.send_message(chat_id, build_links_text(), parse_mode="Markdown")
    except Exception as e:
        log.warning(f"Full welcome failed: {e}")

# ================== JOIN REQUEST HANDLER ==================
async def join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Join request approve + छोटा unlock message भेजना"""
    req = update.chat_join_request
    user = req.from_user

    # Approve request
    try:
        await req.approve()
    except Exception as e:
        log.warning(f"Join approve failed for {user.id}: {e}")
        return

    # Send small unlock message (START दबाने के लिए)
    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=UNLOCK_TEXT_HINDI_EN,
            parse_mode="Markdown"
        )
        log.info(f"Unlock sent to {user.id}")
    except Exception as e:
        log.warning(f"Cannot send unlock message: {e}")

# ================== COMMAND HANDLERS ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User ने START दबाया — अब असली welcome + DB add"""
    upsert_user(update.effective_user)
    cid = update.effective_user.id
    await send_full_welcome(cid, context)


async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    await update.message.reply_text(
        "🛠 *ADMIN PANEL*",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            [
                ["📊 Active Users", "📈 Today Joined"],
                ["👥 Total Users"],
                ["📢 Broadcast", "📤 Forward Broadcast"],
                ["🧹 Delete All", "❌ Cancel"],
            ],
            resize_keyboard=True,
        ),
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    context.user_data.clear()
    await update.message.reply_text("❌ Broadcast Mode OFF")

# ================== DELETE ALL BROADCAST ==================
async def delete_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    deleted = 0
    cursor = broadcasts_col.find({})
    bot = context.bot

    for doc in cursor:
        try:
            await bot.delete_message(doc["chat_id"], doc["message_id"])
            deleted += 1
        except:
            pass

    broadcasts_col.delete_many({})
    await update.message.reply_text(f"🧹 Deleted: {deleted}")

# ================== BROADCAST SYSTEM ==================
async def run_broadcast(context: ContextTypes.DEFAULT_TYPE, users, msgs, reply_msg):
    sent = 0
    fail = 0

    for uid in users:
        try:
            for m in msgs:
                msg_obj = await m.copy(chat_id=uid)
                broadcasts_col.insert_one({
                    "chat_id": uid,
                    "message_id": msg_obj.message_id,
                })
            sent += 1
        except Exception:
            fail += 1
            mark_inactive(uid)

        await asyncio.sleep(0.05)

    await reply_msg.reply_text(f"✔ Sent: {sent}\n❌ Failed: {fail}")

# ================== MAIN ROUTER ==================
async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    user = update.effective_user
    text = msg.text or ""

    # --- Only admin controls ---
    if is_admin(user.id):

        mode = context.user_data.get("mode")

        # Broadcast mode
        if mode == "broadcast":
            msgs = context.user_data["msgs"]

            if text.lower() == "done":
                users = get_active_users()
                await msg.reply_text("📢 Broadcasting…")
                asyncio.create_task(run_broadcast(context, users, msgs, msg))
                context.user_data.clear()
                return

            msgs.append(msg)
            await msg.reply_text(f"Saved ({len(msgs)}) — type DONE when complete")
            return

        # Admin menu
        if text == "📊 Active Users":
            await msg.reply_text(f"Active: {count_active()}")

        elif text == "📈 Today Joined":
            await msg.reply_text(f"Today: {count_today()}")

        elif text == "👥 Total Users":
            await msg.reply_text(f"Total: {count_total()}")

        elif text in ("📢 Broadcast", "📤 Forward Broadcast"):
            context.user_data["mode"] = "broadcast"
            context.user_data["msgs"] = []
            await msg.reply_text("Broadcast Mode ON — send msgs, type DONE when finished")

        elif text == "🧹 Delete All":
            await delete_all(update, context)

        elif text == "❌ Cancel":
            await cancel(update, context)

# ================== RUN BOT ==================
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(ChatJoinRequestHandler(join_request))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("panel", panel))
    app.add_handler(CommandHandler("cancel", cancel))

    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, text_router))

    print("BOT RUNNING…")
    app.run_polling()
