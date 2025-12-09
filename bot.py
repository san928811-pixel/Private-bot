# ================== IMPORTS ==================
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
TOKEN = "8541388990:AAEPBbQhA8jCxA4rlI71gOgOHUWuPS1jVJU"  
MONGO_URI = "mongodb+srv://san928811_db_user:7OufFF7Ux8kOBnrO@cluster0.l1kszyc.mongodb.net/?appName=Cluster0"
ADMIN_IDS = {7895892794}

# 🔥 ONLY CHANGE YOU WANTED — DONE 🔥
BOT_USERNAME = "FastestAutoRequestBot"      # <-- FINAL USERNAME SET

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

# Small unlock message with START button
UNLOCK_TEXT = (
    "🔓 *Unlock Access Required*\n\n"
    "👇 नीचे दिए गए *START* बटन को दबाए बिना आगे कुछ भी दिखाई नहीं देगा।\n"
    "➡️ कृपया तुरंत *START* दबाएँ!\n\n"
    "⭐ शुरू करने के लिए तीन जगह START दिया है:\n"
    "1️⃣ START दबाएँ\n"
    "2️⃣ START now\n"
    "3️⃣ Please tap START\n\n"
    "*English: Press START NOW to unlock access.*\n"
)

# ================== HELPERS ==================
def is_admin(uid: int) -> bool:
    return uid in ADMIN_IDS

def upsert_user(user):
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
    return [d["user_id"] for d in users_col.find({"active": True}, {"user_id": 1})]

def count_active():
    return users_col.count_documents({"active": True})

def count_total():
    return users_col.count_documents({})

def count_today():
    today = datetime.utcnow().date()
    start = datetime(today.year, today.month, today.day)
    end = start + timedelta(days=1)
    return users_col.count_documents({"joined_at": {"$gte": start, "$lt": end}, "active": True})

# ================== MESSAGES ==================
def build_links_text():
    txt = "🔗 *Important Links*\n\n"
    for name, link in CHANNEL_LINKS:
        txt += f"• {name} – {link}\n"
    return txt

def build_start_keyboard():
    url = f"https://t.me/{BOT_USERNAME}?start=start"
    return InlineKeyboardMarkup([[InlineKeyboardButton("▶️ START NOW", url=url)]])

async def send_full_welcome(chat_id, context):
    await context.bot.send_message(chat_id, WELCOME_TEXT, parse_mode="Markdown")
    await context.bot.send_message(chat_id, build_links_text(), parse_mode="Markdown")

# ================== BROADCAST WORKER ==================
async def run_broadcast(context, users, msgs, reply_msg):
    sent = 0
    failed = 0
    for uid in users:
        try:
            for m in msgs:
                sent_msg = await m.copy(chat_id=uid)
                broadcasts_col.insert_one(
                    {"chat_id": uid, "message_id": sent_msg.message_id, "created_at": datetime.utcnow()}
                )
            sent += 1
        except Exception:
            failed += 1
            mark_inactive(uid)
        await asyncio.sleep(0.05)

    await reply_msg.reply_text(f"📢 Broadcast Completed!\n✔ Sent: {sent}\n❌ Failed: {failed}")

# ================== HANDLERS ==================
async def join_request(update, context):
    req = update.chat_join_request
    user = req.from_user
    try:
        await req.approve()
    except:
        return

    # Send unlock message with START button
    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=UNLOCK_TEXT,
            parse_mode="Markdown",
            reply_markup=build_start_keyboard(),
        )
    except:
        pass

async def start(update, context):
    upsert_user(update.effective_user)
    await send_full_welcome(update.effective_user.id, context)

async def panel(update, context):
    if not is_admin(update.effective_user.id):
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

async def cancel(update, context):
    if not is_admin(update.effective_user.id):
        return
    context.user_data.clear()
    await update.message.reply_text("❌ Broadcast Mode OFF")

async def delete_all(update, context):
    deleted = 0
    cursor = broadcasts_col.find({})
    for doc in cursor:
        try:
            await context.bot.delete_message(doc["chat_id"], doc["message_id"])
            deleted += 1
        except:
            pass
    broadcasts_col.delete_many({})
    await update.message.reply_text(f"🧹 Deleted: {deleted}")

async def text_router(update, context):
    msg = update.message
    if not msg:
        return

    user = update.effective_user
    text = msg.text or ""

    users_col.update_one({"user_id": user.id}, {"$set": {"last_active": datetime.utcnow()}})

    if not is_admin(user.id):
        return

    mode = context.user_data.get("mode")

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
            await msg.reply_text("Limit reached, type DONE")
        return

    if text in ("📢 Broadcast", "📤 Forward Broadcast"):
        context.user_data["mode"] = "broadcast"
        context.user_data["msgs"] = []
        await msg.reply_text("📢 Broadcast Mode ON\nSend msgs now.\nType DONE to start.")

    elif text == "📊 Active Users":
        await msg.reply_text(f"Active: {count_active()}")

    elif text == "📈 Today Joined":
        await msg.reply_text(f"Today: {count_today()}")

    elif text == "👥 Total Users":
        await msg.reply_text(f"Total: {count_total()}")

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
