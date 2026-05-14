import os
import json
import random
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# ===================== SOZLAMALAR =====================
BOT_TOKEN = "8636477180:AAGNTGfnkST5uM4SdUuzNV3NCZcYIigkqk4"
KANAL = "@pdf_audio_kitobz"
ADMIN_ID = 1217116376  # BU YERGA O'Z TELEGRAM ID'INGIZNI YOZING

KATEGORIYALAR = [
    "Biznes", "Psixologiya", "Roman",
    "Tarix", "Ilm-fan", "Motivatsiya",
    "Dasturlash", "Falsafa", "Boshqa"
]

KITOBLAR_FAYL = "kitoblar.json"

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# ===================== KITOBLAR BAZASI =====================
def kitoblar_yukla():
    if os.path.exists(KITOBLAR_FAYL):
        with open(KITOBLAR_FAYL, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def kitoblar_saqlа(kitoblar):
    with open(KITOBLAR_FAYL, "w", encoding="utf-8") as f:
        json.dump(kitoblar, f, ensure_ascii=False, indent=2)

# ===================== ADMIN TEKSHIRISH =====================
def admin_mi(user_id):
    return user_id == ADMIN_ID

# ===================== START =====================
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    tugmalar = [
        [InlineKeyboardButton("📚 Barcha kitoblar", callback_data="barchasi")],
        [InlineKeyboardButton("🔍 Kategoriya", callback_data="kategoriya")],
        [InlineKeyboardButton("🆕 Oxirgi kitoblar", callback_data="oxirgi")],
    ]
    await update.message.reply_text(
        "📚 *Kitoblar Olamiga xush kelibsiz!*\n\n"
        "Bu yerda PDF va Audio kitoblarni bepul yuklab olasiz.\n\n"
        "Quyidagi bo'limlardan birini tanlang 👇",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(tugmalar)
    )

# ===================== KITOBLAR RO'YXATI =====================
async def barchasi_korsат(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    kitoblar = kitoblar_yukla()
    query = update.callback_query
    await query.answer()

    if not kitoblar:
        await query.edit_message_text("📭 Hozircha kitoblar yo'q. Tez orada qo'shiladi!")
        return

    matn = "📚 *Barcha kitoblar:*\n\n"
    tugmalar = []
    for i, k in enumerate(kitoblar):
        matn += f"{i+1}. {k['nom']} — _{k['kategoriya']}_\n"
        tugmalar.append([InlineKeyboardButton(f"📖 {k['nom']}", callback_data=f"kitob_{i}")])

    tugmalar.append([InlineKeyboardButton("🔙 Orqaga", callback_data="start")])
    await query.edit_message_text(matn, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(tugmalar))

# ===================== KATEGORIYA =====================
async def kategoriya_korsат(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    tugmalar = []
    for kat in KATEGORIYALAR:
        tugmalar.append([InlineKeyboardButton(f"📂 {kat}", callback_data=f"kat_{kat}")])
    tugmalar.append([InlineKeyboardButton("🔙 Orqaga", callback_data="start")])

    await query.edit_message_text(
        "📂 *Kategoriyani tanlang:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(tugmalar)
    )

async def kategoriya_kitoblar(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kat = query.data.replace("kat_", "")

    kitoblar = kitoblar_yukla()
    kat_kitoblar = [k for k in kitoblar if k["kategoriya"] == kat]

    if not kat_kitoblar:
        await query.edit_message_text(f"📭 {kat} kategoriyasida hozircha kitob yo'q.")
        return

    tugmalar = []
    for i, k in enumerate(kitoblar):
        if k["kategoriya"] == kat:
            tugmalar.append([InlineKeyboardButton(f"📖 {k['nom']}", callback_data=f"kitob_{i}")])

    tugmalar.append([InlineKeyboardButton("🔙 Orqaga", callback_data="kategoriya")])
    await query.edit_message_text(
        f"📂 *{kat}* kategoriyasidagi kitoblar:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(tugmalar)
    )

# ===================== OXIRGI KITOBLAR =====================
async def oxirgi_kitoblar(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    kitoblar = kitoblar_yukla()
    oxirgi = kitoblar[-5:] if len(kitoblar) >= 5 else kitoblar
    oxirgi = list(reversed(oxirgi))

    if not oxirgi:
        await query.edit_message_text("📭 Hozircha kitoblar yo'q.")
        return

    tugmalar = []
    for k in oxirgi:
        idx = kitoblar.index(k)
        tugmalar.append([InlineKeyboardButton(f"📖 {k['nom']}", callback_data=f"kitob_{idx}")])

    tugmalar.append([InlineKeyboardButton("🔙 Orqaga", callback_data="start")])
    await query.edit_message_text(
        "🆕 *Oxirgi qo'shilgan kitoblar:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(tugmalar)
    )

# ===================== KITOB YUBORISH =====================
async def kitob_yuborish(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    idx = int(query.data.replace("kitob_", ""))
    kitoblar = kitoblar_yukla()

    if idx >= len(kitoblar):
        await query.edit_message_text("❌ Kitob topilmadi.")
        return

    k = kitoblar[idx]
    await query.edit_message_text(
        f"📖 *{k['nom']}*\n"
        f"📂 Kategoriya: {k['kategoriya']}\n"
        f"📅 Qo'shilgan: {k['sana']}\n\n"
        "Quyidagi formatni tanlang 👇",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📄 PDF", callback_data=f"pdf_{idx}") if k.get("pdf_id") else InlineKeyboardButton("❌ PDF yo'q", callback_data="yoq"),
                InlineKeyboardButton("🎧 Audio", callback_data=f"audio_{idx}") if k.get("audio_id") else InlineKeyboardButton("❌ Audio yo'q", callback_data="yoq"),
            ],
            [InlineKeyboardButton("🔙 Orqaga", callback_data="barchasi")]
        ])
    )

async def pdf_yuborish(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    idx = int(query.data.replace("pdf_", ""))
    kitoblar = kitoblar_yukla()
    k = kitoblar[idx]
    await ctx.bot.send_document(
        chat_id=query.message.chat_id,
        document=k["pdf_id"],
        caption=f"📄 *{k['nom']}*\n📂 {k['kategoriya']}\n\n📚 @pdf_audio_kitobz",
        parse_mode="Markdown"
    )

async def audio_yuborish(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    idx = int(query.data.replace("audio_", ""))
    kitoblar = kitoblar_yukla()
    k = kitoblar[idx]
    await ctx.bot.send_audio(
        chat_id=query.message.chat_id,
        audio=k["audio_id"],
        caption=f"🎧 *{k['nom']}*\n📂 {k['kategoriya']}\n\n📚 @pdf_audio_kitobz",
        parse_mode="Markdown"
    )

# ===================== ADMIN — KITOB QO'SHISH =====================
async def admin_buyruq(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not admin_mi(update.message.from_user.id):
        return

    await update.message.reply_text(
        "👨‍💼 *Admin panel*\n\n"
        "Kitob qo'shish uchun:\n\n"
        "1️⃣ PDF yuborish: Menga PDF faylni yuboring\n"
        "2️⃣ Audio yuborish: Menga audio faylni yuboring\n\n"
        "Fayl yuborganingizdan so'ng nom va kategoriyasini so'rayman.",
        parse_mode="Markdown"
    )

# ===================== FAYL QABUL QILISH =====================
async def fayl_qabul(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
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
        await msg.reply_text("❌ Faqat PDF yoki Audio fayl yuboring.")
        return

    ctx.user_data["fayl_id"] = fayl_id
    ctx.user_data["fayl_tur"] = fayl_tur

    tugmalar = [[InlineKeyboardButton(kat, callback_data=f"newkat_{kat}")] for kat in KATEGORIYALAR]
    await msg.reply_text(
        f"✅ {'PDF' if fayl_tur == 'pdf' else 'Audio'} qabul qilindi!\n\n"
        "📝 Kitob nomini yozing:",
        parse_mode="Markdown"
    )
    ctx.user_data["holat"] = "nom_kutish"

async def matn_qabul(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not admin_mi(update.message.from_user.id):
        return

    holat = ctx.user_data.get("holat")

    if holat == "nom_kutish":
        ctx.user_data["kitob_nom"] = update.message.text
        ctx.user_data["holat"] = "kategoriya_kutish"

        tugmalar = [[InlineKeyboardButton(f"📂 {kat}", callback_data=f"newkat_{kat}")] for kat in KATEGORIYALAR]
        await update.message.reply_text(
            "📂 Kategoriyani tanlang:",
            reply_markup=InlineKeyboardMarkup(tugmalar)
        )

async def kategoriya_tanlash(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not admin_mi(query.from_user.id):
        return

    kat = query.data.replace("newkat_", "")
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
        yangi = {
            "nom": nom,
            "kategoriya": kat,
            "sana": datetime.now().strftime("%Y-%m-%d"),
            "pdf_id": fayl_id if fayl_tur == "pdf" else None,
            "audio_id": fayl_id if fayl_tur == "audio" else None,
        }
        kitoblar.append(yangi)

    kitoblar_saqlа(kitoblar)
    ctx.user_data.clear()

    await query.edit_message_text(
        f"✅ *{nom}* kitob qo'shildi!\n"
        f"📂 Kategoriya: {kat}\n"
        f"{'📄 PDF' if fayl_tur == 'pdf' else '🎧 Audio'} saqlandi.",
        parse_mode="Markdown"
    )

# ===================== HAR SOATDA KAНАЛГА YUBORISH =====================
async def soatlik_yuborish(ctx: ContextTypes.DEFAULT_TYPE):
    kitoblar = kitoblar_yukla()
    if not kitoblar:
        return

    k = random.choice(kitoblar)

    matn = (
        f"📚 *{k['nom']}*\n"
        f"📂 Kategoriya: {k['kategoriya']}\n\n"
        f"📥 Kitobni olish uchun botga yozing:\n"
        f"👉 @pdf_audio_kitobz_bot\n\n"
        f"#kitob #{k['kategoriya'].lower()} #bepulkitob #pdf #audiokitob"
    )

    try:
        if k.get("pdf_id"):
            await ctx.bot.send_document(
                chat_id=KANAL,
                document=k["pdf_id"],
                caption=matn,
                parse_mode="Markdown"
            )
        elif k.get("audio_id"):
            await ctx.bot.send_audio(
                chat_id=KANAL,
                audio=k["audio_id"],
                caption=matn,
                parse_mode="Markdown"
            )
    except Exception as e:
        log.error(f"Kaналга yuborishda xato: {e}")

# ===================== CALLBACK HANDLER =====================
async def callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data == "start":
        await start_callback(update, ctx)
    elif data == "barchasi":
        await barchasi_korsат(update, ctx)
    elif data == "kategoriya":
        await kategoriya_korsат(update, ctx)
    elif data == "oxirgi":
        await oxirgi_kitoblar(update, ctx)
    elif data.startswith("kat_"):
        await kategoriya_kitoblar(update, ctx)
    elif data.startswith("kitob_"):
        await kitob_yuborish(update, ctx)
    elif data.startswith("pdf_"):
        await pdf_yuborish(update, ctx)
    elif data.startswith("audio_"):
        await audio_yuborish(update, ctx)
    elif data.startswith("newkat_"):
        await kategoriya_tanlash(update, ctx)
    elif data == "yoq":
        await query.answer("Bu format mavjud emas", show_alert=True)

async def start_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    tugmalar = [
        [InlineKeyboardButton("📚 Barcha kitoblar", callback_data="barchasi")],
        [InlineKeyboardButton("🔍 Kategoriya", callback_data="kategoriya")],
        [InlineKeyboardButton("🆕 Oxirgi kitoblar", callback_data="oxirgi")],
    ]
    await query.edit_message_text(
        "📚 *Kitoblar Olamiga xush kelibsiz!*\n\n"
        "Quyidagi bo'limlardan birini tanlang 👇",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(tugmalar)
    )

# ===================== ASOSIY =====================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Handlerlar
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_buyruq))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.Document.PDF | filters.AUDIO, fayl_qabul))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, matn_qabul))

    # Har soatda yuborish (3600 sekund)
    app.job_queue.run_repeating(soatlik_yuborish, interval=3600, first=10)

    print("🤖 Bot ishga tushdi!")
    app.run_polling()

if __name__ == "__main__":
    main()
