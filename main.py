import os
import re
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ======================
# 1. سيرفر وهمي لـ Render (عشان ما ينام)
# ======================
app = Flask(__name__)

@app.route('/')
def home():
    return "Al Haris Bot V10.2 is Running 🛡️"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# ======================
# 2. محرك كشف النصب (بالدلالة - يشتغل بدون نت)
# ======================
def check_scam(text):
    text_low = text.lower()
    
    # تحويل الأرقام العربية ٠١٢٣ إلى إنجليزية
    trans = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
    text_low = text_low.translate(trans).replace(",", "").replace("٬", "")

    score = 0
    reasons = []

    # دلالات النصب (حتى بدون مبلغ)
    LURE_WORDS = {
        "رصيد": 3, "منحة": 3, "منحه": 3, "دراسية": 2, "دراسيه": 2, "جامعية": 2,
        "هدية": 3, "هبه": 3, "مجانا": 3, "مجانية": 3, "مبروك": 3,
        "ربحت": 4, "فزت": 4, "فائز": 3, "تم اختيارك": 4, "اختيارك": 2,
        "سجل": 2, "سجّل": 2, "التسجيل": 2, "انضم": 2, "شارك": 1,
        "فرصة": 2, "فرصه": 2, "عاجل": 2, "فوري": 2, "محدود": 2,
        "تواصل": 2, "منظمة": 2
    }
    
    for word, pts in LURE_WORDS.items():
        if word in text_low:
            score += pts
            reasons.append(f"دلالة: {word} (+{pts})")

    # وجود أي رقم (حتى بدون كلمة ريال) - 10، 100، 5000
    if re.search(r'\b\d{2,}\b', text_low):
        score += 2
        reasons.append("يحتوي على رقم/مبلغ")

    # رابط + طلب تسجيل = نصب كلاسيكي
    has_link = bool(re.search(r'https?://|www\.|bit\.ly|tinyurl|t\.me|cutt\.ly', text_low))
    has_register = any(x in text_low for x in ["سجل", "اضغط", "رابط", "ادخل", "قدم", "انقر"])
    
    if has_link and has_register:
        score += 4
        reasons.append("رابط + طلب تسجيل/ضغط")

    # الدومينات المنتهية (قضية twasel.com اللي اكتشفتها)
    if any(x in text_low for x in ["is for sale", "hugedomains", "buy now", "domain for sale"]):
        score += 5
        reasons.append("⚠️ دومين منتهي ومعروض للبيع")

    # الحكم
    if score >= 5:
        return f"🚨 نصب مؤكد ({score} نقاط):\n" + "\n".join(reasons)
    elif score >= 3:
        return f"⚠️ مشبوه جداً ({score} نقاط):\n" + "\n".join(reasons)
    elif score >= 2:
        return f"⚠️ مشبوه ({score} نقاط):\n" + "\n".join(reasons)
    else:
        return "✅ آمن نسبياً - لم أجد دلالات نصب واضحة"

# ======================
# 3. أوامر التيليجرام
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🛡️ أهلاً بك في **الحارس - Al Haris**\n\n"
        "أرسل لي أي رسالة أو رابط وسأفحصه لك فوراً.\n\n"
        "مثال للتجربة:\n"
        "`منحة دراسية سجل الآن 5000`\n"
        "`رصيد مجاني اضغط الرابط`\n"
        "`www.twasel.com`\n\n"
        "البوت يشتغل بالدلالة، حتى بدون ذكر ريال."
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = check_scam(update.message.text)
    await update.message.reply_text(result)

def run_bot():
    TOKEN = os.environ.get("BOT_TOKEN")
    if not TOKEN:
        print("❌ BOT_TOKEN غير موجود في Environment Variables")
        return
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 البوت بدأ...")
    application.run_polling()

# ======================
# 4. التشغيل
# ======================
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    run_bot()
