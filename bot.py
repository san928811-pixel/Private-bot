from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Set

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

# ============== CONFIG ==============

# ⚠️ अपना BOT TOKEN यहाँ रखो (किसी और को मत भेजना)
TOKEN = "7936792037:AAEY8w1SamkAangZr66Lbfd_DKUK0GUzC18"

# 👉 यहाँ अपने और बाकी admins के Telegram user IDs डालो
ADMINS: Set[int] = {
    7895892794,  # आप
    # 123456789, # दूसरा admin (जरूरत हो तो add कर लेना)
}

# Users / Info / Banned users
USERS: Set[int] = set()
USER_INFO: Dict[int, Dict[str, Any]] = {}
BANNED: Set[int] = set()

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
log = logging.getLogger(__name__)


# ============== HELPER FUNCTIONS ==============

def add_or_update_user(update: Update) -> int | None:
    """User list + info update करता है."""
    user = update.effective_user
    if not user:
        return None

    uid = user.id
    now = datetime.now(timezone.utc)

    if uid not in USERS:
        USERS.add(uid)
        USER_INFO[uid] = {
            "first_name": user.first_name or "",
            "joined": now,
            "last_seen": now,
        }
    else:
        info = USER_INFO.get(uid)
        if info is not None:
            info["last_seen"] = now
        else:
            USER_INFO[uid] = {
                "first_name": user.first_name or "",
                "joined": now,
                "last_seen": now,
            }
    return uid


def is_admin(uid: int) -> bool:
    return uid in ADMINS


def is_banned(uid: int) -> bool:
    return uid in BANNED


# ============== COMMAND HANDLERS ==============

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = add_or_update_user(update)
    if uid is None:
        return

    if is_banned(uid):
        # banned users को ignore
        return

    # Success message
    await update.message.reply_text("✅ Bot successfully चल रहा है!")

    # Welcome message
    welcome_text = (
        "👋 *Welcome to Anjali Ki Duniya*\n\n"
        "⏳  आपको थोड़ी देर बाद यहाँ *Best Collection Videos* के अपडेट "
        "मिलने शुरू हो जाएंगे।"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")


# /admin – admin panel with buttons
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id
    add_or_update_user(update)

    if not is_admin(uid):
        return await update.message.reply_text("❌ आप admin नहीं हैं।")

    keyboard = [
        [
            InlineKeyboardButton("📊 Total Users", callback_data="stats_total"),
            InlineKeyboardButton("🧮 Today Join", callback_data="stats_today"),
        ],
        [
            InlineKeyboardButton("🟢 Online (5 min)", callback_data="stats_online"),
        ],
        [
            InlineKeyboardButton("🚫 Banned Count", callback_data="stats_banned"),
        ],
        [
            InlineKeyboardButton("ℹ️ Help", callback_data="admin_help"),
        ],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🛠 *Admin Panel*", reply_markup=markup, parse_mode="Markdown")


# Admin panel button callbacks
async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    uid = query.from_user.id
    if not is_admin(uid):
        return await query.edit_message_text("❌ आप admin नहीं हैं।")

    now = datetime.now(timezone.utc)
    data = query.data

    if data == "stats_total":
        total = len(USERS)
        await query.edit_message_text(f"📊 Total users: *{total}*", parse_mode="Markdown")

    elif data == "stats_today":
        today = now.date()
        count_today = sum(
            1
            for info in USER_INFO.values()
            if isinstance(info.get("joined"), datetime) and info["joined"].date() == today
        )
        await query.edit_message_text(
            f"🧮 आज जुड़े हुए users: *{count_today}*", parse_mode="Markdown"
        )

    elif data == "stats_online":
        online_count = 0
        for info in USER_INFO.values():
            last = info.get("last_seen")
            if isinstance(last, datetime) and now - last <= timedelta(minutes=5):
                online_count += 1
        await query.edit_message_text(
            f"🟢 लगभग online users (पिछले 5 मिनट में active): *{online_count}*",
            parse_mode="Markdown",
        )

    elif data == "stats_banned":
        await query.edit_message_text(
            f"🚫 Banned users count: *{len(BANNED)}*", parse_mode="Markdown"
        )

    elif data == "admin_help":
        help_text = (
            "⚙️ *Admin Help*\n\n"
            "/admin – Admin panel\n"
            "/broadcast <text> – Text broadcast\n"
            "/ban <user_id> – User ban (broadcast नहीं जाएगा)\n"
            "/unban <user_id> – Ban हटाओ\n\n"
            "📢 *Forward Broadcast*: किसी भी message/photo/video को "
            "bot को forward करो → सब users को forward हो जाएगा।"
        )
        await query.edit_message_text(help_text, parse_mode="Markdown")


# /broadcast <text> – admin text broadcast
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id
    add_or_update_user(update)

    if not is_admin(uid):
        return await update.message.reply_text("❌ आप admin नहीं हैं।")

    text = " ".join(context.args)
    if not text:
        return await update.message.reply_text("ℹ️ Usage: `/broadcast आपका message`", parse_mode="Markdown")

    sent = 0
    for user_id in list(USERS):
        if is_banned(user_id):
            continue
        try:
            await context.bot.send_message(chat_id=user_id, text=text)
            sent += 1
        except Exception as e:
            log.warning("Broadcast failed to %s: %s", user_id, e)

    await update.message.reply_text(f"📢 Broadcast भेज दी गई ✅ ({sent} users)")


# /ban <user_id>
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id
    if not is_admin(uid):
        return

    if not context.args:
        return await update.message.reply_text("Usage: /ban <user_id>")

    try:
        target = int(context.args[0])
    except ValueError:
        return await update.message.reply_text("❌ गलत user_id")

    BANNED.add(target)
    USERS.discard(target)
    await update.message.reply_text(f"🚫 User `{target}` banned.", parse_mode="Markdown")


# /unban <user_id>
async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id
    if not is_admin(uid):
        return

    if not context.args:
        return await update.message.reply_text("Usage: /unban <user_id>")

    try:
        target = int(context.args[0])
    except ValueError:
        return await update.message.reply_text("❌ गलत user_id")

    if target in BANNED:
        BANNED.remove(target)
        await update.message.reply_text(f"✅ User `{target}` unbanned.", parse_mode="Markdown")
    else:
        await update.message.reply_text("ℹ️ ये user banned list में नहीं है।")


# ============== FORWARD BROADCAST ==============

# कोई भी forward किया हुआ message → सबको forward
async def forward_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id
    add_or_update_user(update)

    # सिर्फ admins ही forward broadcast कर सकें
    if not is_admin(uid):
        return

    if not update.message:
        return

    sent = 0
    for user_id in list(USERS):
        if is_banned(user_id):
            continue
        try:
            await update.message.forward(chat_id=user_id)
            sent += 1
        except Exception as e:
            log.warning("Forward broadcast failed to %s: %s", user_id, e)

    await update.message.reply_text(f"📢 Forward Broadcast भेज दी गई ✅ ({sent} users)")


# ============== NORMAL USER MESSAGES ==============

# Normal users के सभी messages ignore (no chat)
async def user_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = add_or_update_user(update)
    if uid is None:
        return

    if is_banned(uid):
        # banned user – पूरी तरह ignore
        return

    if is_admin(uid):
        # admin chat को allow कर सकते हो (अभी ignore कर रहे हैं)
        return

    # Normal users के लिए – simply ignore so कि bot सिर्फ broadcast bot रहे
    return


# ============== MAIN ==============

def main() -> None:
    app = ApplicationBuilder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("unban", unban_user))

    # Admin panel buttons
    app.add_handler(CallbackQueryHandler(admin_buttons))

    # Forward broadcast – सिर्फ forwarded message पर
    app.add_handler(MessageHandler(filters.FORWARDED & filters.ALL, forward_broadcast))

    # बाकी सारे text/photo/video आदि – normal users के लिए ignore
    app.add_handler(MessageHandler(~filters.COMMAND, user_message))

    log.info("Bot starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
