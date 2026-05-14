import os
import json
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import (
    Updater, CommandHandler, MessageHandler,
    CallbackQueryHandler, Filters, CallbackContext
)

# ===================== SOZLAMALAR =====================
BOT_TOKEN = "8636477180:AAGNTGfnkST5uM4SdUuzNV3NCZcYIigkqk4"
GURUH_ID = -10039667095  # Guruh ID (raqam)
GURUH_LINK = "https://t.me/pdf_audio_kitobz"
ADMIN_ID = 1217116376

KATEGORIYALAR = [
    "Biznes", "Psixologiya", "Roman",
    "Tarix", "Ilm-fan", "Motivatsiya",
    "Dasturlash", "Falsafa", "Boshqa"
]

KITOBLAR_FAYL = "kitoblar.json"
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# ===================== YORDAMCHI =====================
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

def guruh_azosimi(bot, user_id):
    try:
        member = bot.get_chat_member(GURUH_ID, user_id)
        return member.status in [
            ChatMember.MEMBER,
            ChatMember.ADMINISTRATOR,
            ChatMember.CREATOR
        ]
    except:
        return False

def guruhga_qoshiling_xabari(update):
    tugma = [[InlineKeyboardButton(
        "Guruhga qo'shiling",
        url=GURUH_LINK
    )]]
    update.message.reply_text(
        "Botdan to'liq foydalanish uchun avval guruhimizga qo'shiling!\n\n"
        "Qo'shilgach, kitob nomini yozing.",
        reply_markup=InlineKeyboardMarkup(tugma)
    )

# ===================== START =====================
def start(update: Update, ctx: CallbackContext):
    update.message.reply_text(
        "Kitoblar Olamiga xush kelibsiz!\n\n"
        "Qidirmoqchi bo'lgan kitob nomini yozing.\n\n"
        "Masalan: Atomic Habits"
    )

# ===================== KITOB QIDIRISH =====================
def kitob_qidir(update: Update, ctx: CallbackContext):
    user_id = update.message.from_user.id
    matn = update.message.text.strip()

    if admin_mi(user_id):
        if ctx.user_data.get("holat") == "nom_kutish":
            ctx.user_data["kitob_nom"] = matn
            ctx.user_data["holat"] = "kategoriya_kutish"
            tugmalar = [[InlineKeyboardButton(kat, callback_data=f"newkat_{kat}")] for kat in KATEGORIYALAR]
            update.message.reply_text("Kategoriyani tanlang:", reply_markup=InlineKeyboardMarkup(tugmalar))
            return

    if not guruh_azosimi(ctx.bot, user_id):
        guruhga_qoshiling_xabari(update)
        return

    kitoblar = kitoblar_yukla()
    natijalar = [
        (i, k) for i, k in enumerate(kitoblar)
        if matn.lower() in k["nom"].lower()
    ]

    if not natijalar:
        tugma = [[InlineKeyboardButton("Guruhga o'tish", url=GURUH_LINK)]]
        update.message.reply_text(
            f"'{matn}' kitob topilmadi.\n\n"
            "Guruhimizdan qidiring, u yerda ko'proq kitoblar bor!",
            reply_markup=InlineKeyboardMarkup(tugma)
        )
        return

    tugmalar = [[InlineKeyboardButton(k["nom"], callback_data=f"kitob_{i}")] for i, k in natijalar]
    update.message.reply_text(
        f"'{matn}' bo'yicha natijalar:",
        reply_markup=InlineKeyboardMarkup(tugmalar)
    )

# ===================== ADMIN =====================
def admin_buyruq(update: Update, ctx: CallbackContext):
    if not admin_mi(update.message.from_user.id):
        return
    update.message.reply_text(
        "Admin panel\n\n"
        "Kitob qo'shish uchun PDF yoki Audio fayl yuboring."
    )

def fayl_qabul(update: Update, ctx: CallbackContext):
    if not admin_mi(update.message.from_user.id):
        return
    msg = update.message
    if msg.document:
        ctx.user_data["fayl_id"] = msg.document.file_id
        ctx.user_data["fayl_tur"] = "pdf"
    elif msg.audio:
        ctx.user_data["fayl_id"] = msg.audio.file_id
        ctx.user_data["fayl_tur"] = "audio"
    else:
        msg.reply_text("Faqat PDF yoki Audio fayl yuboring.")
        return
    ctx.user_data["holat"] = "nom_kutish"
    msg.reply_text("Fayl qabul qilindi! Kitob nomini yozing:")

# ===================== CALLBACK =====================
def callback_handler(update: Update, ctx: CallbackContext):
    query = update.callback_query
    query.answer()
    data = query.data

    if data.startswith("kitob_"):
        idx = int(data.replace("kitob_", ""))
        kitoblar = kitoblar_yukla()
        if idx >= len(kitoblar):
            query.edit_message_text("Kitob topilmadi.")
            return
        k = kitoblar[idx]
        row = []
        if k.get("pdf_id"):
            row.append(InlineKeyboardButton("PDF yuklab ol", callback_data=f"pdf_{idx}"))
        if k.get("audio_id"):
            row.append(InlineKeyboardButton("Audio tingla", callback_data=f"audio_{idx}"))
        tugmalar = [row]
        query.edit_message_text(
            f"{k['nom']}\nKategoriya: {k['kategoriya']}\nSana: {k['sana']}\n\nFormatni tanlang:",
            reply_markup=InlineKeyboardMarkup(tugmalar)
        )

    elif data.startswith("pdf_"):
        idx = int(data.replace("pdf_", ""))
        kitoblar = kitoblar_yukla()
        k = kitoblar[idx]
        ctx.bot.send_document(
            chat_id=query.message.chat_id,
            document=k["pdf_id"],
            caption=f"{k['nom']}\n{k['kategoriya']}\n\n@pdf_audio_kitobz"
        )

    elif data.startswith("audio_"):
        idx = int(data.replace("audio_", ""))
        kitoblar = kitoblar_yukla()
        k = kitoblar[idx]
        ctx.bot.send_audio(
            chat_id=query.message.chat_id,
            audio=k["audio_id"],
            caption=f"{k['nom']}\n{k['kategoriya']}\n\n@pdf_audio_kitobz"
        )

    elif data.startswith("newkat_") and admin_mi(query.from_user.id):
        kat = data.replace("newkat_", "")
        fayl_id = ctx.user_data.get("fayl_id")
        fayl_tur = ctx.user_data.get("fayl_tur")
        nom = ctx.user_data.get("kitob_nom", "Nomsiz")
        kitoblar = kitoblar_yukla()
        mavjud = next((k for k in kitoblar if k["nom"].lower() == nom.lower()), None)
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
        query.edit_message_text(f"{nom} muvaffaqiyatli saqlandi!\nKategoriya: {kat}")

# ===================== ASOSIY =====================
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("admin", admin_buyruq))
    dp.add_handler(CallbackQueryHandler(callback_handler))
    dp.add_handler(MessageHandler(Filters.document | Filters.audio, fayl_qabul))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, kitob_qidir))

    print("Bot ishga tushdi!")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
