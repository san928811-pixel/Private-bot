from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ==== YOUR BOT TOKEN ====
TOKEN = "7936792037:AAEY8w1SamKAanqZr66Lbfd_DKUK0GUzC18"

# ==== ADMINS LIST (यहाँ अपने + admin के Telegram ID डालो) ====
ADMINS = [7895892794]   # तुम अपना ID यहाँ डालकर बाकी admin भी जोड़ सकते हो

# ==== USERS DATABASE ====
USERS = set()


# ===================== START COMMAND =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id
    USERS.add(uid)      # user को database में जोड़ दिया

    welcome_msg = (
        "👋 *Welcome to Anjali Ki Duniya*\n\n"
        "⏳ आपको थोड़ी देर बाद यहाँ Best Collection Videos के अपडेट मिलने शुरू हो जाएंगे।"
    )

    await update.message.reply_text(welcome_msg, parse_mode="Markdown")


# ===================== ADMIN PANEL =====================
async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id
    if uid not in ADMINS:
        return  # Non-admin को panel नहीं मिलेगा

    keyboard = [
        [InlineKeyboardButton("📊 Total Users", callback_data="total")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")],
        [InlineKeyboardButton("❌ Fake Report Block", callback_data="blockfake")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🛠 Admin Control Panel", reply_markup=reply_markup)


# ===================== BUTTON HANDLER =====================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    uid = query.from_user.id

    await query.answer()

    # सिर्फ एडमिन ही बटन का उपयोग कर सकते हैं
    if uid not in ADMINS:
        return

    # ----- TOTAL USERS -----
    if query.data == "total":
        await query.edit_message_text(f"📊 *Total Users:* {len(USERS)}", parse_mode="Markdown")

    # ----- BROADCAST MODE -----
    elif query.data == "broadcast":
        await query.edit_message_text("📢 *Broadcast Mode ON*\nमुझे कोई भी संदेश भेजो, वह सभी users को चला जाएगा।", parse_mode="Markdown")
        context.user_data["broadcast"] = True

    # ----- BLOCK FAKE REPORT USERS -----
    elif query.data == "blockfake":
        await query.edit_message_text("❌ Fake reporting करने वाले users को auto-remove किया जाएगा।")
        # (यह feature सक्रिय है — message handler में काम करेगा)


# ===================== BROADCAST MESSAGE =====================
async def broadcast_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id

    if uid in ADMINS and context.user_data.get("broadcast"):

        sent = 0
        for user in USERS:
            try:
                await context.bot.send_message(chat_id=user, text=update.message.text)
                sent += 1
            except:
                pass

        await update.message.reply_text(f"📢 Broadcast sent to {sent} users.")
        context.user_data["broadcast"] = False
    else:
        return


# ===================== FAKE REPORT FILTER =====================
async def fake_report_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.lower()

    # यदि user Spam / Report / Fake report की बात करे ⇒ Auto Block
    if any(word in text for word in ["spam", "report", "fake report", "fir"]):
        uid = update.effective_user.id
        if uid in USERS:
            USERS.remove(uid)
            await update.message.reply_text("❌ आपकी suspicious activity के कारण आपको bot से हटा दिया गया है।")
        return


# ===================== RUN BOT =====================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("panel", panel))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fake_report_filter))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_msg))

    app.add_handler(MessageHandler(filters.COMMAND, broadcast_msg))
    app.add_handler(MessageHandler(filters.ALL, broadcast_msg))
    
    app.add_handler(MessageHandler(filters.ALL, broadcast_msg))

    app.add_handler(CommandHandler("panel", panel))

    app.add_handler(MessageHandler(filters.ALL, broadcast_msg))

    app.add_handler(CommandHandler("panel", panel))

    app.add_handler(MessageHandler(filters.ALL, broadcast_msg))

    app.add_handler(CommandHandler("panel", panel))

    app.add_handler(MessageHandler(filters.ALL, broadcast_msg))

    app.add_handler(CommandHandler("panel", panel))

    app.add_handler(MessageHandler(filters.ALL, broadcast_msg))

    app.add_handler(CommandHandler("panel", panel))

    app.add_handler(MessageHandler(filters.ALL, broadcast_msg))

    app.add_handler(CommandHandler("panel", panel))

    app.add_handler(MessageHandler(filters.ALL, broadcast_msg))

    app.add_handler(CommandHandler("panel", panel))

    app.add_handler(MessageHandler(filters.ALL, broadcast_msg))

    # callback handler
    from telegram.ext import CallbackQueryHandler
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()


if __name__ == "__main__":
    main()
