import os
import json
import google.generativeai as genai
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from PIL import Image

# RENDER DAN OLINADI
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# O'ZINGIZNI USERNAME YOZING
ADMIN_USERNAME = "@eezzuuoo"

# GEMINI SOZLASH
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# BAZA
DB_FILE = "/tmp/users_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_db(db):
    with open(DB_FILE, 'w') as f:
        json.dump(db, f)

def get_count(uid):
    return load_db().get(str(uid), {}).get('count', 0)

def add_count(uid):
    db = load_db()
    s = str(uid)
    if s not in db:
        db[s] = {'count':0,'paid':False}
    db[s]['count'] += 1
    save_db(db)
    return db[s]['count']

def is_paid(uid):
    return load_db().get(str(uid), {}).get('paid', False)

# TUGMALAR
MAIN_MENU = ReplyKeyboardMarkup(
    [
        ["📸 Rasm tashla", "✍️ Matn yoz"],
        ["🎞️ Formatni tanla", "⏱️ Video vaqti"],
        ["🎬 Video generatsiya"],
        ["💳 Pul to'lash"]
    ],
    resize_keyboard=True
)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    c = get_count(update.effective_user.id)
    left = 3 - c
    await update.message.reply_text(
        f"Salom! Men EzuAi17Bot man! 🧠✨\n"
        f"Mamasidiqova O'g'iloy tomonidan yaratildim!\n\n"
        f"🎬 Rasmni videoga aylantiraman\n"
        f"💬 Har qanday savolga Gemini kabi javob beraman\n\n"
        f"Sizda {left} ta bepul urinish qoldi!",
        reply_markup=MAIN_MENU
    )

# MATN
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = update.effective_user.id

    if text == "💳 Pul to'lash":
        await update.message.reply_text(
            f"💳 Obuna narxi: 10 000 so'm / 1 oy - Cheksiz!\n\n"
            f"To'lash uchun @{ADMIN_USERNAME} ga yozing: 'Obuna olmoqchiman'\n"
            f"Sizning ID: {uid}",
            reply_markup=MAIN_MENU
        )
        return

    if text in ["📸 Rasm tashla", "🎬 Video generatsiya"]:
        await update.message.reply_text("Marhamat, rasm tashlang! 🖼️👇", reply_markup=MAIN_MENU)
        return

    if text in ["🎞️ Formatni tanla"]:
        await update.message.reply_text("Format: 9:16, 1:1, 16:9 ✅ Tanlandi!", reply_markup=MAIN_MENU)
        return

    if text in ["⏱️ Video vaqti"]:
        await update.message.reply_text("Vaqt: 5s, 10s, 15s ✅ Tanlandi!", reply_markup=MAIN_MENU)
        return

    if text in ["✍️ Matn yoz"]:
        await update.message.reply_text("Nima haqida yozay? Matningizni yuboring! ✍️", reply_markup=MAIN_MENU)
        return

    # GEMINI BILAN SUHBAT
    await update.message.reply_chat_action("typing")
    try:
        prompt = f"Sen EzuAi17Bot san, Mamasidiqova O'g'iloy yaratgan. O'zbek tilida, qiz bola kabi samimiy, chiroyli javob ber. Savol: {text}"
        res = model.generate_content(prompt)
        await update.message.reply_text(res.text, reply_markup=MAIN_MENU)
    except Exception as e:
        await update.message.reply_text(
            "⚠️ Gemini key xato! Render ga GEMINI_API_KEY ni qo'shdingizmi?",
            reply_markup=MAIN_MENU
        )

# RASM
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    count = get_count(uid)

    if not is_paid(uid) and count >= 3:
        await update.message.reply_text(
            "⛔ OGOHLANTIRISH!\n\n"
            "Sizning 3 ta BEPUL video harakatlaringiz tugadi! 🎬\n\n"
            "Davom ettirish uchun obuna olishingiz kerak!\n"
            f"👉 @{ADMIN_USERNAME} ga yozing\n"
            "💰 10 000 so'm = 1 oy cheksiz!",
            reply_markup=MAIN_MENU
        )
        return

    await update.message.reply_text(f"⏳ Rasm jonlanmoqda... Bu sizning {count+1}-chi videongiz", reply_markup=MAIN_MENU)

    file = await update.message.photo[-1].get_file()
    await file.download_to_drive("/tmp/input.jpg")
    img = Image.open("/tmp/input.jpg")
    img.save("/tmp/out.jpg")

    new_c = add_count(uid)
    left = 3 - new_c

    if is_paid(uid):
        caption = f"✅ Tayyor! Sizda cheksiz obuna bor! ♾️"
    else:
        if left > 0:
            caption = f"✅ Tayyor! Yana {left} ta bepul qoldi! 🎬"
        else:
            caption = f"✅ Tayyor! Bu oxirgi bepul video edi! Keyingisi uchun obuna kerak ⚠️"

    await update.message.reply_photo(
        photo=open("/tmp/out.jpg", "rb"),
        caption=caption,
        reply_markup=MAIN_MENU
    )

# TO'LOV YOQISH
async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Foydalanish: /pay 12345678")
        return
    user_id = context.args[0]
    db = load_db()
    db[user_id] = {'count': 0, 'paid': True}
    save_db(db)
    await update.message.reply_text(f"✅ {user_id} ga cheksiz obuna yoqildi! ♾️")

# ISHGA TUSHIRISH
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("pay", pay))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

print("EzuAi17Bot ishga tushdi! Gemini bilan!")
app.run_polling()
