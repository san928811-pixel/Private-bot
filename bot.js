const { Telegraf, Markup } = require("telegraf");

// =========================
// BOT TOKEN (यहीं अपना token डालना है)
// =========================
const BOT_TOKEN = "8563001384:AAGm-bHjgj8uydURUfv_TISDrrrHFFmerL0";   // <-- यहाँ अपना पूरा BotFather token डालना
const bot = new Telegraf(BOT_TOKEN);

// =========================
// ADMIN USERNAME
// =========================
const ADMIN = "@Shwetakumari89";

// =========================
// ALL PLANS MENU
// =========================
const plansMenu = Markup.inlineKeyboard([
  [Markup.button.callback("1️⃣ Basic – ₹299 | 15 USDT", "basic")],
  [Markup.button.callback("2️⃣ Advanced – ₹499 | 20 USDT", "advanced")],
  [Markup.button.callback("3️⃣ Pro – ₹999 | 30 USDT", "pro")],
  [Markup.button.callback("4️⃣ Combo – ₹1599 | 40 USDT", "combo")],
  [Markup.button.callback("5️⃣ Ultra Max – ₹1999 | 60 USDT", "ultra")],
]);

// =========================
// START MESSAGE
// =========================
bot.start((ctx) =>
  ctx.reply(
`👋 Welcome to **VIP Premium Membership Bot**

💎 Features:
• Premium Membership Plans  
• Fast Activation  
• Secure Payment  
• 24×7 Support

⭐ Plans (India + International)
1️⃣ Basic — ₹299 | 15 USDT  
2️⃣ Advanced — ₹499 | 20 USDT  
3️⃣ Pro — ₹999 | 30 USDT  
4️⃣ Combo — ₹1599 | 40 USDT  
5️⃣ Ultra Max — ₹1999 | 60 USDT

👇 नीचे से अपना प्लान चुनें:
`,
    plansMenu
  )
);

// =========================
// PAYMENT PAGE
// =========================
function sendPlan(ctx, title, inr, usdt) {
  ctx.reply(
`🔷 Selected Plan: ${title}

💰 Price:
🇮🇳 India: ₹${inr}  
🌍 International: ${usdt} USDT

-----------------------------------------

💳 PAYMENT OPTIONS

🇮🇳 INDIA (UPI)
UPI ID: 78753256788@kotak

🌍 INTERNATIONAL PAYMENT
Use:
• LiPay  
• PaySend  
• Remitly  
• USDT (TRC20)

USDT Address:
Txxxxxxxxxxxxxxxxxxxxx

-----------------------------------------

📌 IMPORTANT

Payment करने के बाद:
1) Screenshot  
2) Telegram Username  
👉 भेजें: ${ADMIN}

Verification के बाद access दे दिया जाएगा.
⏳ Time: 1–10 minutes
`,
    Markup.inlineKeyboard([
      [Markup.button.callback("📋 Copy UPI", "copy_upi")],
      [Markup.button.callback("🌎 Copy USDT Address", "copy_usdt")],
      [Markup.button.url("✔ I Paid — Send Screenshot", `https://t.me/${ADMIN.replace("@", "")}`)],
      [Markup.button.callback("🔙 Back to Plans", "back")],
    ])
  );
}

// =========================
// PLAN ACTION HANDLERS
// =========================
bot.action("basic", (ctx) => sendPlan(ctx, "Basic Plan (1 Month)", 299, 15));
bot.action("advanced", (ctx) => sendPlan(ctx, "Advanced Plan (Lifetime)", 499, 20));
bot.action("pro", (ctx) => sendPlan(ctx, "Pro Plan (Lifetime)", 999, 30));
bot.action("combo", (ctx) => sendPlan(ctx, "Combo Plan (Lifetime)", 1599, 40));
bot.action("ultra", (ctx) => sendPlan(ctx, "Ultra Max (Lifetime)", 1999, 60));

// =========================
// EASY COPY BUTTONS
// =========================
bot.action("copy_upi", (ctx) => {
  ctx.reply(
    "📋 *UPI ID (Long-press करके कॉपी करें)*\n`78753256788@kotak`",
    { parse_mode: "Markdown" }
  );
});

bot.action("copy_usdt", (ctx) => {
  ctx.reply(
    "🌍 *USDT (TRC20) Address*\n`Txxxxxxxxxxxxxxxxxxxxx`",
    { parse_mode: "Markdown" }
  );
});

// =========================
// BACK BUTTON
// =========================
bot.action("back", (ctx) =>
  ctx.reply("⬅ Back to Plans", plansMenu)
);

// =========================
// RUN BOT
// =========================
bot.launch();
console.log("🚀 VIP Premium Bot Running…");
