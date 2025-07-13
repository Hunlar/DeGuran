import json
import os
import random
import requests
import schedule
import time
import threading
from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton, Bot
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters
)

TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROUPS_FILE = "groups.json"

bot = Bot(token=TOKEN)

def save_group(chat_id):
    try:
        with open(GROUPS_FILE, "r", encoding="utf-8") as f:
            groups = json.load(f)
    except FileNotFoundError:
        groups = []

    if chat_id not in groups:
        groups.append(chat_id)
        with open(GROUPS_FILE, "w", encoding="utf-8") as f:
            json.dump(groups, f, ensure_ascii=False)

def get_random_ayah():
    ayah_number = random.randint(1, 6236)
    arabic_url = f"https://api.alquran.cloud/v1/ayah/{ayah_number}"
    turkish_url = f"https://api.alquran.cloud/v1/ayah/{ayah_number}/tr.duz"

    arabic_response = requests.get(arabic_url).json()
    turkish_response = requests.get(turkish_url).json()

    if arabic_response["status"] == "OK" and turkish_response["status"] == "OK":
        surah = arabic_response["data"]["surah"]["name"]
        num = arabic_response["data"]["numberInSurah"]
        arabic = arabic_response["data"]["text"]
        turkish = turkish_response["data"]["text"]
        return f"📖 *{surah} Suresi {num}. Ayet*\n\n🔹 _{arabic}_\n\n💬 {turkish}"
    return "⚠️ Ayet alınamadı."

def send_to_all_groups():
    try:
        with open(GROUPS_FILE, "r", encoding="utf-8") as f:
            groups = json.load(f)
    except FileNotFoundError:
        groups = []

    message = get_random_ayah()
    for chat_id in groups:
        try:
            bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
        except Exception as e:
            print(f"⚠️ Hata: {e} - {chat_id}")

def start_scheduler():
    schedule.every().hour.at(":00").do(send_to_all_groups)
    while True:
        schedule.run_pending()
        time.sleep(1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ayasofya_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/1/10/Hagia_Sophia_Mars_2020_img1.jpg/640px-Hagia_Sophia_Mars_2020_img1.jpg"
    keyboard = [
        [InlineKeyboardButton("Destek Grubu", url="https://t.me/Kizilsancaktr")],
        [InlineKeyboardButton("ZEYD BİN SABR", url="https://t.me/zeydbinhalit")]
    ]
    caption = (
        "🕌 Bu bot, hayatın yoğun temposunda Kur’an’ı Kerim’i ve İslamiyet’i hatırlatmak "
        "ve yaymak amacıyla yapılmıştır."
    )
    await update.message.reply_photo(
        photo=ayasofya_url,
        caption=caption,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def ayet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = get_random_ayah()
    await update.message.reply_text(message, parse_mode="Markdown")

async def ara(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("🔎 Kullanım: /ara kelime")
        return

    query = " ".join(context.args)
    url = f"https://api.alquran.cloud/v1/search/{query}/all/tr.duz"
    response = requests.get(url).json()

    if response["status"] != "OK" or response["data"]["count"] == 0:
        await update.message.reply_text("❌ Uygun sonuç bulunamadı.")
        return

    results = response["data"]["matches"][:3]
    reply = f"🔍 *{query}* için bulunan ayetler:\n\n"
    for match in results:
        surah = match["surah"]["name"]
        num = match["numberInSurah"]
        text = match["text"]
        reply += f"*{surah}* - {num}. Ayet\n💬 {text}\n\n"

    await update.message.reply_text(reply.strip(), parse_mode="Markdown")

# ✅ Ali Hadis API'den rastgele hadis
async def hadis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        kaynak = "abu-dawud"
        max_num = 500
        num = random.randint(1, max_num)

        url = f"https://api.sutanlab.id/hadith/{kaynak}/{num}"
        response = requests.get(url).json()

        if response["status"] != "OK":
            await update.message.reply_text("❌ Hadis verisi alınamadı.")
            return

        hadis = response["data"]
        metin = hadis.get("arab") or hadis.get("id") or "Hadis metni yok."
        kaynak_bilgi = f"{hadis['name']}, No: {hadis['number']}"

        await update.message.reply_text(f"📜 \"{metin}\"\n\n📚 {kaynak_bilgi}")
    except Exception as e:
        print("Hata:", e)
        await update.message.reply_text("⚠️ Bir hata oluştu, lütfen daha sonra tekrar deneyin.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in ["group", "supergroup"]:
        save_group(update.effective_chat.id)

def start_bot():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ayet", ayet))
    app.add_handler(CommandHandler("ara", ara))
    app.add_handler(CommandHandler("hadis", hadis))
    app.add_handler(MessageHandler(filters.ALL, handle_message))

    app.run_polling()

threading.Thread(target=start_scheduler).start()
start_bot()
