import os
import json
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# ===================== SOZLAMALAR =====================
BOT_TOKEN = "8636477180:AAGNTGfnkST5uM4SdUuzNV3NCZcYIigkqk4"
GURUH_ID = -1003966708795
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

async def guruh_azosimi(bot, user_id):
    try:
        member = await bot.get_chat_member(GURUH_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Kitoblar Olamiga xush kelibsiz!\n\n"
        "Qidirmoqchi bolgan kitob nomini yozing.\n\n"
        "Masalan: Atomic Habits"
    )

async def admin_buyruq(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not admin_mi(update.message.from_user.id):
        return
    await update.message.reply_text(
        "Admin panel\n\n"
        "Kitob qoshish uchun PDF yoki Audio fayl yuboring."
    )

async def fayl_qabul(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
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
        await msg.reply_text("Faqat PDF yoki Audio fayl yuboring.")
        return
    ctx.user_data["holat"] = "nom_kutish"
    await msg.reply_text("Fayl qabul qilindi! Kitob nomini yozing:")

async def matn_qabul(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    matn = update.message.text.strip()

    if admin_mi(user_id) and ctx.user_data.get("holat") == "nom_kutish":
        ctx.user_data["kitob_nom"] = matn
        ctx.user_data["holat"] = "kategoriya_kutish"
        tugmalar = [[InlineKeyboardButton(kat, callback_data=f"newkat_{kat}")] for kat in KATEGORIYALAR]
        await update.message.reply_text("Kategoriyani tanlang:", reply_markup=InlineKeyboardMarkup(tugmalar))
        return

    if not await guruh_azosimi(ctx.bot, user_id):
        tugma = [[InlineKeyboardButton("Guruhga qoshiling", url=GURUH_LINK)]]
        await update.message.reply_text(
            "Botdan toliq foydalanish uchun avval guruhimizga qoshiling!",
            reply_markup=InlineKeyboardMarkup(tugma)
        )
        return

    kitoblar = kitoblar_yukla()
    natijalar = [(i, k) for i, k in enumerate(kitoblar) if matn.lower() in k["nom"].lower()]

    if not natijalar:
        tugma = [[InlineKeyboardButton("Guruhga otish", url=GURUH_LINK)]]
        await update.message.reply_text(
            f"'{matn}' kitob topilmadi.\nGuruhimizdan qidiring!",
            reply_markup=InlineKeyboardMarkup(tugma)
        )
        return

    tugmalar = [[InlineKeyboardButton(k["nom"], callback_data=f"kitob_{i}")] for i, k in natijalar]
    await update.message.reply_text("Natijalar:", reply_markup=InlineKeyboardMarkup(tugmalar))

async def callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("kitob_"):
        idx = int(data.replace("kitob_", ""))
        kitoblar = kitoblar_yukla()
        if idx >= len(kitoblar):
            await query.edit_message_text("Kitob topilmadi.")
            return
        k = kitoblar[idx]
        row = []
        if k.get("pdf_id"):
            row.append(InlineKeyboardButton("PDF yuklab ol", callback_data=f"pdf_{idx}"))
        if k.get("audio_id"):
            row.append(InlineKeyboardButton("Audio tingla", callback_data=f"audio_{idx}"))
        await query.edit_message_text(
            f"{k['nom']}\nKategoriya: {k['kategoriya']}\n\nFormatni tanlang:",
            reply_markup=InlineKeyboardMarkup([row])
        )

    elif data.startswith("pdf_"):
        idx = int(data.replace("pdf_", ""))
        kitoblar = kitoblar_yukla()
        k = kitoblar[idx]
        await ctx.bot.send_document(
            chat_id=query.message.chat_id,
            document=k["pdf_id"],
            caption=f"{k['nom']}\n{k['kategoriya']}\n\n@pdf_audio_kitobz"
        )

    elif data.startswith("audio_"):
        idx = int(data.replace("audio_", ""))
        kitoblar = kitoblar_yukla()
        k = kitoblar[idx]
        await ctx.bot.send_audio(
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
        await query.edit_message_text(f"{nom} saqlandi! Kategoriya: {kat}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_buyruq))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.AUDIO, fayl_qabul))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, matn_qabul))
    print("Bot ishga tushdi!")
    app.run_polling()

if __name__ == "__main__":
    main()
