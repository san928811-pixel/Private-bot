# ================== IMPORTS ==================
import logging
import asyncio
from datetime import datetime, timedelta

from telegram import (
    Update,
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

BOT_USERNAME = "YourBotUsername"   # <-- सिर्फ username (without @)

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

# Small unlock message (Hindi + English + 3 बार START highlight)
UNLOCK_TEXT = (
    "🔓 *Unlock Access Required*\n\n"
    "👇 नीचे दिए गए *START* बटन को दबाए बिना आगे कुछ नहीं दिखेगा।\n"
    "➡️ कृपया तुरंत *START* दबाएँ!\n\n"
    "⭐ आसान बनाने के लिए यहाँ 3 जगह START लिखा है:\n"
    "1️⃣ START दबाएँ और आगे बढ़ें\n"
    "2️⃣ START without delay\n"
    "3️⃣ Please tap START to continue\n\n"
    "*English:*\n"
    "Tap the *START NOW* button below 👇\n"
)

# ================== DB ==================
client = MongoClient(MONGO_URI, server_api=ServerApi("1"))
db = client["anjali_bot"]
users_col = db["users"]
broadcasts_col = db["broadcasts"]

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


# ================== HELPER FUNCTIONS ==================
def is_admin(uid): return uid in ADMIN_IDS


def upsert_user(u):
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


def mark_inactive(uid):
    users_col.update_one({"user_id": uid}, {"$set": {"active": False}})


def get_active_users():
    return [u["user_id"] for u in users_col.find({"active": True})]


def count_active(): return users_col.count_documents({"active": True})
def count_today():
    today = datetime.utcnow().date()
    start = datetime(today.year, today.month, today.day)
    return users_col.count_documents(
        {"joined_at": {"$gte": start}, "active": True}
    )
def count_total(): return users_col.count_documents({})


# ================== BUTTONS ==================
def build_start_button():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "▶️ START NOW",
            url=f"https://t.me/{BOT_USERNAME}?start=start"
        )]
    ])


def build_links_text():
    txt = "🔗 *Important Links*\n\n"
    for name, link in CHANNEL_LINKS:
        txt += f"• {name} – {link}\n"
    return txt


async def send_welcome(chat_id, context):
    await context.bot.send_message(chat_id, WELCOME_TEXT, parse_mode="Markdown")
    await context.bot.send_message(chat_id, build_links_text(), parse_mode="Markdown")


# ================== JOIN REQUEST HANDLER ==================
async def join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    req = update.chat_join_request
    user = req.from_user

    upsert_user(user)

    try:
        await req.approve()
    except:
        return

    # Send unlock message + start button
    await context.bot.send_message(
        chat_id=user.id,
        text=UNLOCK_TEXT,
        parse_mode="Markdown",
        reply_markup=build_start_button()
    )


# ================== /START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    upsert_user(update.effective_user)
    await send_welcome(update.effective_user.id, context)


# ================== PANEL ==================
async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    await update.message.reply_text(
        f"👥 Active: {count_active()}\n"
        f"📈 Today Joined: {count_today()}\n"
        f"📌 Total Users: {count_total()}",
    )


# ================== BROADCAST ==================
async def text_router(update: Update, context):
    msg = update.message
    if not msg:
        return

    user = update.effective_user
    upsert_user(user)

    if not is_admin(user.id):
        return

    # Start broadcast
    if msg.text == "broadcast":
        context.user_data["mode"] = "broadcast"
        context.user_data["msgs"] = []
        await msg.reply_text("📢 Send messages for broadcast.\nType DONE when finished.")
        return

    # Save broadcast messages
    if context.user_data.get("mode") == "broadcast":
        if msg.text.lower() == "done":
            users = get_active_users()
            await msg.reply_text("⏳ Broadcasting…")
            asyncio.create_task(run_broadcast(context, users, context.user_data["msgs"], msg))
            context.user_data.clear()
            return

        context.user_data["msgs"].append(msg)
        await msg.reply_text("✔ Saved. Send more or type DONE.")
        return


async def run_broadcast(context, users, msgs, reply_msg):
    sent = 0
    failed = 0

    for uid in users:
        try:
            for m in msgs:
                await m.copy(chat_id=uid)
            sent += 1
        except:
            failed += 1
            mark_inactive(uid)

    await reply_msg.reply_text(f"📢 Done!\n✔ Sent: {sent}\n❌ Failed: {failed}")


# ================== RUN ==================
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("panel", panel))
    app.add_handler(ChatJoinRequestHandler(join_request))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, text_router))

    print("BOT RUNNING…")
    app.run_polling()
