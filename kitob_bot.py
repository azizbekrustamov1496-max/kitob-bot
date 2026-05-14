import os
import json
import random
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater, CommandHandler, MessageHandler,
    CallbackQueryHandler, Filters, CallbackContext
)
from apscheduler.schedulers.background import BackgroundScheduler

# ===================== SOZLAMALAR =====================
BOT_TOKEN = "8636477180:AAGNTGfnkST5uM4SdUuzNV3NCZcYIigkqk4"
KANAL = "@pdf_audio_kitobz"
ADMIN_ID = 1217116376

KATEGORIYALAR = [
    "Biznes", "Psixologiya", "Roman",
    "Tarix", "Ilm-fan", "Motivatsiya",
    "Dasturlash", "Falsafa", "Boshqa"
]

KITOBLAR_FAYL = "kitoblar.json"
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def kitoblar_yukla():
    if os.path.exists(KITOBLAR_FAYL):
        with open(KITOBLAR_FAYL, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def kitoblar_saqlа(kitoblar):
    with open(KITOBLAR_FAYL, "w", encoding="utf-8") as f:
        json.dump(kitoblar, f, ensure_ascii=False, indent=2)

def admin_mi(user_id):
    return user_id == ADMIN_ID

def start(update: Update, ctx: CallbackContext):
    tugmalar = [
        [InlineKeyboardButton("📚 Barcha kitoblar", callback_data="barchasi")],
        [InlineKeyboardButton("🔍 Kategoriya", callback_data="kategoriya")],
        [InlineKeyboardButton("🆕 Oxirgi kitoblar", callback_data="oxirgi")],
    ]
    update.message.reply_text(
        "📚 *Kitoblar Olamiga xush kelibsiz!*\n\n"
        "PDF va Audio kitoblarni bepul yuklab oling.\n\n"
        "Quyidagi bo'limlardan birini tanlang 👇",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(tugmalar)
    )

def admin_buyruq(update: Update, ctx: CallbackContext):
    if not admin_mi(update.message.from_user.id):
        return
    update.message.reply_text(
        "👨\u200d💼 *Admin panel*\n\n"
        "Kitob qo'shish:\n"
        "1️⃣ PDF yoki Audio fayl yuboring\n"
        "2️⃣ Kitob nomini yozing\n"
        "3️⃣ Kategoriya tanlang",
        parse_mode="Markdown"
    )

def fayl_qabul(update: Update, ctx: CallbackContext):
    if not admin_mi(update.message.from_user.id):
        return
    msg = update.message
    fayl_id = None
    fayl_tur = None
    if msg.document and msg.document.mime_type == "application/pdf":
        fayl_id = msg.document.file_id
        fayl_tur = "pdf"
    elif msg.audio:
        fayl_id = msg.audio.file_id
        fayl_tur = "audio"
    else:
        msg.reply_text("Faqat PDF yoki Audio yuboring.")
        return
    ctx.user_data["fayl_id"] = fayl_id
    ctx.user_data["fayl_tur"] = fayl_tur
    ctx.user_data["holat"] = "nom_kutish"
    msg.reply_text(f"✅ {'PDF' if fayl_tur == 'pdf' else 'Audio'} qabul qilindi!\n\n📝 Kitob nomini yozing:")

def matn_qabul(update: Update, ctx: CallbackContext):
    if not admin_mi(update.message.from_user.id):
        return
    if ctx.user_data.get("holat") != "nom_kutish":
        return
    ctx.user_data["kitob_nom"] = update.message.text
    ctx.user_data["holat"] = "kategoriya_kutish"
    tugmalar = [[InlineKeyboardButton(f"📂 {kat}", callback_data=f"newkat_{kat}")] for kat in KATEGORIYALAR]
    update.message.reply_text("📂 Kategoriyani tanlang:", reply_markup=InlineKeyboardMarkup(tugmalar))

def callback_handler(update: Update, ctx: CallbackContext):
    query = update.callback_query
    query.answer()
    data = query.data

    if data == "barchasi":
        kitoblar = kitoblar_yukla()
        if not kitoblar:
            query.edit_message_text("📭 Hozircha kitoblar yo'q.")
            return
        tugmalar = [[InlineKeyboardButton(f"📖 {k['nom']}", callback_data=f"kitob_{i}")] for i, k in enumerate(kitoblar)]
        tugmalar.append([InlineKeyboardButton("🔙 Orqaga", callback_data="start")])
        query.edit_message_text("📚 *Barcha kitoblar:*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(tugmalar))

    elif data == "kategoriya":
        tugmalar = [[InlineKeyboardButton(f"📂 {kat}", callback_data=f"kat_{kat}")] for kat in KATEGORIYALAR]
        tugmalar.append([InlineKeyboardButton("🔙 Orqaga", callback_data="start")])
        query.edit_message_text("📂 *Kategoriyani tanlang:*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(tugmalar))

    elif data == "oxirgi":
        kitoblar = kitoblar_yukla()
        if not kitoblar:
            query.edit_message_text("📭 Hozircha kitoblar yo'q.")
            return
        oxirgi = list(enumerate(kitoblar))[-5:][::-1]
        tugmalar = [[InlineKeyboardButton(f"📖 {k['nom']}", callback_data=f"kitob_{i}")] for i, k in oxirgi]
        tugmalar.append([InlineKeyboardButton("🔙 Orqaga", callback_data="start")])
        query.edit_message_text("🆕 *Oxirgi kitoblar:*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(tugmalar))

    elif data == "start":
        tugmalar = [
            [InlineKeyboardButton("📚 Barcha kitoblar", callback_data="barchasi")],
            [InlineKeyboardButton("🔍 Kategoriya", callback_data="kategoriya")],
            [InlineKeyboardButton("🆕 Oxirgi kitoblar", callback_data="oxirgi")],
        ]
        query.edit_message_text(
            "📚 *Kitoblar Olamiga xush kelibsiz!*\n\nQuyidagi bo'limlardan birini tanlang 👇",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(tugmalar)
        )

    elif data.startswith("kat_"):
        kat = data.replace("kat_", "")
        kitoblar = kitoblar_yukla()
        kat_list = [(i, k) for i, k in enumerate(kitoblar) if k["kategoriya"] == kat]
        if not kat_list:
            query.edit_message_text(f"📭 {kat} kategoriyasida kitob yo'q.")
            return
        tugmalar = [[InlineKeyboardButton(f"📖 {k['nom']}", callback_data=f"kitob_{i}")] for i, k in kat_list]
        tugmalar.append([InlineKeyboardButton("🔙 Orqaga", callback_data="kategoriya")])
        query.edit_message_text(f"📂 *{kat}:*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(tugmalar))

    elif data.startswith("kitob_"):
        idx = int(data.replace("kitob_", ""))
        kitoblar = kitoblar_yukla()
        if idx >= len(kitoblar):
            query.edit_message_text("❌ Kitob topilmadi.")
            return
        k = kitoblar[idx]
        row = []
        if k.get("pdf_id"):
            row.append(InlineKeyboardButton("📄 PDF", callback_data=f"pdf_{idx}"))
        if k.get("audio_id"):
            row.append(InlineKeyboardButton("🎧 Audio", callback_data=f"audio_{idx}"))
        tugmalar = [row, [InlineKeyboardButton("🔙 Orqaga", callback_data="barchasi")]]
        query.edit_message_text(
            f"📖 *{k['nom']}*\n📂 {k['kategoriya']}\n📅 {k['sana']}\n\nFormatni tanlang 👇",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(tugmalar)
        )

    elif data.startswith("pdf_"):
        idx = int(data.replace("pdf_", ""))
        kitoblar = kitoblar_yukla()
        k = kitoblar[idx]
        ctx.bot.send_document(
            chat_id=query.message.chat_id,
            document=k["pdf_id"],
            caption=f"📄 *{k['nom']}*\n📂 {k['kategoriya']}\n\n📚 @pdf_audio_kitobz",
            parse_mode="Markdown"
        )

    elif data.startswith("audio_"):
        idx = int(data.replace("audio_", ""))
        kitoblar = kitoblar_yukla()
        k = kitoblar[idx]
        ctx.bot.send_audio(
            chat_id=query.message.chat_id,
            audio=k["audio_id"],
            caption=f"🎧 *{k['nom']}*\n📂 {k['kategoriya']}\n\n📚 @pdf_audio_kitobz",
            parse_mode="Markdown"
        )

    elif data.startswith("newkat_") and admin_mi(query.from_user.id):
        kat = data.replace("newkat_", "")
        fayl_id = ctx.user_data.get("fayl_id")
        fayl_tur = ctx.user_data.get("fayl_tur")
        nom = ctx.user_data.get("kitob_nom", "Nomsiz")
        kitoblar = kitoblar_yukla()
        mavjud = next((k for k in kitoblar if k["nom"] == nom), None)
        if mavjud:
            if fayl_tur == "pdf":
                mavjud["pdf_id"] = fayl_id
            else:
                mavjud["audio_id"] = fayl_id
        else:
            kitoblar.append({
                "nom": nom,
                "kategoriya": kat,
                "sana": datetime.now().strftime("%Y-%m-%d"),
                "pdf_id": fayl_id if fayl_tur == "pdf" else None,
                "audio_id": fayl_id if fayl_tur == "audio" else None,
            })
        kitoblar_saqlа(kitoblar)
        ctx.user_data.clear()
        query.edit_message_text(f"✅ *{nom}* saqlandi!\n📂 {kat}", parse_mode="Markdown")

def soatlik_yuborish(bot):
    kitoblar = kitoblar_yukla()
    if not kitoblar:
        return
    k = random.choice(kitoblar)
    matn = (
        f"📚 *{k['nom']}*\n"
        f"📂 Kategoriya: {k['kategoriya']}\n\n"
        f"📥 Kitobni olish uchun botga yozing:\n"
        f"👉 @KitobxonUz_bot\n\n"
        f"#kitob #bepulkitob #pdf #audiokitob"
    )
    try:
        if k.get("pdf_id"):
            bot.send_document(chat_id=KANAL, document=k["pdf_id"], caption=matn, parse_mode="Markdown")
        elif k.get("audio_id"):
            bot.send_audio(chat_id=KANAL, audio=k["audio_id"], caption=matn, parse_mode="Markdown")
    except Exception as e:
        log.error(f"Xato: {e}")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("admin", admin_buyruq))
    dp.add_handler(CallbackQueryHandler(callback_handler))
    dp.add_handler(MessageHandler(Filters.document | Filters.audio, fayl_qabul))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, matn_qabul))

    scheduler = BackgroundScheduler()
    scheduler.add_job(soatlik_yuborish, "interval", hours=1, args=[updater.bot])
    scheduler.start()

    print("Bot ishga tushdi!")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
