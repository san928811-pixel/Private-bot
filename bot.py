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

# ================== DB ==================
client = MongoClient(MONGO_URI, server_api=ServerApi("1"))
db = client["anjali_bot"]
users_col = db["users"]

# ================== LOGGING ==================
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# ================== HELPERS ==================
def is_admin(uid): return uid in ADMIN_IDS

def upsert_user(u):
    if not u:
        return
    users_col.update_one(
        {"user_id": u.id},
        {"$set": {
            "first_name": u.first_name,
            "username": u.username,
            "active": True,
            "last_active": datetime.utcnow(),
        },
         "$setOnInsert": {"joined_at": datetime.utcnow()}
         },
        upsert=True,
    )

def mark_inactive(uid):
    users_col.update_one({"user_id": uid}, {"$set": {"active": False}})

def get_active_users():
    return [u["user_id"] for u in users_col.find({"active": True})]

# ================== WELCOME MESSAGE ==================
def build_links_text():
    t = "🔗 *Important Links*\n\n"
    for name, link in CHANNEL_LINKS:
        t += f"• [{name}]({link})\n"
    return t

async def send_welcome(chat_id, context):
    await context.bot.send_message(chat_id, WELCOME_TEXT, parse_mode="Markdown")
    await context.bot.send_message(chat_id, build_links_text(), parse_mode="Markdown")

# ================== BACKGROUND BROADCAST ==================
async def run_broadcast(context, users, msgs, reply_msg):
    sent = 0
    fail = 0

    for uid in users:
        try:
            for m in msgs:
                await m.copy(chat_id=uid)
            sent += 1
        except:
            fail += 1
            mark_inactive(uid)

        await asyncio.sleep(0.05)

    await reply_msg.reply_text(f"📢 Broadcast Completed!\n✔ Sent: {sent}\n❌ Failed: {fail}")

# ================== COMMANDS ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    upsert_user(update.effective_user)
    cid = update.effective_user.id

    await send_welcome(cid, context)

async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    kb = ReplyKeyboardMarkup(
        [["📊 Total Users", "📈 Today Joined"],
         ["📢 Broadcast"],
         ["❌ Cancel"]],
        resize_keyboard=True
    )
    await update.message.reply_text("🛠 *ADMIN PANEL*", parse_mode="Markdown", reply_markup=kb)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Broadcast Mode OFF")

async def join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    req = update.chat_join_request
    u = req.from_user

    upsert_user(u)

    try: await req.approve()
    except: return

    try: await send_welcome(u.id, context)
    except: pass

# ================== MAIN TEXT ROUTER ==================
async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    user = update.effective_user
    text = msg.text or ""

    upsert_user(user)

    if not is_admin(user.id):  
        return

    # ---------------- Broadcast Mode ----------------
    if context.user_data.get("mode") == "broadcast":
        msgs = context.user_data["msgs"]

        if text.lower() == "done":
            users = get_active_users()
            await msg.reply_text("📢 Broadcasting started…")

            asyncio.create_task(run_broadcast(context, users, msgs, msg))

            context.user_data.clear()
            return

        # Save message
        msgs.append(msg)
        await msg.reply_text(f"📩 Message saved ({len(msgs)})\nType DONE when finished.")
        return

    # ---------------- Admin Menu ----------------
    if text == "📢 Broadcast":
        context.user_data["mode"] = "broadcast"
        context.user_data["msgs"] = []
        await msg.reply_text("📢 Broadcast Mode ON\nSend up to 10 messages, then type DONE.")
        return

    if text == "📊 Total Users":
        total = users_col.count_documents({"active": True})
        await msg.reply_text(f"👥 Total Users: {total}")

    if text == "📈 Today Joined":
        today = datetime.utcnow().date()
        start = datetime(today.year, today.month, today.day)
        end = start + timedelta(days=1)
        count = users_col.count_documents({"joined_at": {"$gte": start, "$lt": end}})
        await msg.reply_text(f"📈 Today Joined: {count}")

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
