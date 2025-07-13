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

# Grup ID'si kaydet
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

# Ayet çek
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

# Hadisleri JSON'dan yükle
def load_hadisler():
    try:
        with open("hadisler.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

# Tüm gruplara ayet gönder
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

# Saat başı gönderim için zamanlayıcı
def start_scheduler():
    schedule.every().hour.at(":00").do(send_to_all_groups)
    while True:
        schedule.run_pending()
        time.sleep(1)

# /start komutu
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

# /ayet komutu
async def ayet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = get_random_ayah()
    await update.message.reply_text(message, parse_mode="Markdown")

# /ara komutu
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

    results = response["data"]["matches"][:3]  # İlk 3 sonucu göster
    reply = f"🔍 *{query}* için bulunan ayetler:\n\n"
    for match in results:
        surah = match["surah"]["name"]
        num = match["numberInSurah"]
        text = match["text"]
        reply += f"*{surah}* - {num}. Ayet\n💬 {text}\n\n"

    await update.message.reply_text(reply.strip(), parse_mode="Markdown")

# /hadis komutu
async def hadis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hadisler = load_hadisler()
    if not hadisler:
        await update.message.reply_text("⚠️ Hadis verisi bulunamadı.")
        return
    hadis = random.choice(hadisler)
    await update.message.reply_text(f"📜 \"{hadis['metin']}\"\n\n📚 {hadis['kaynak']}")

# Grup mesajı gelince grup ID'sini kaydet
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in ["group", "supergroup"]:
        save_group(update.effective_chat.id)

# Telegram botunu başlat
def start_bot():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ayet", ayet))
    app.add_handler(CommandHandler("ara", ara))
    app.add_handler(CommandHandler("hadis", hadis))
    app.add_handler(MessageHandler(filters.ALL, handle_message))

    app.run_polling()

# Scheduler ve botu başlat
threading.Thread(target=start_scheduler).start()
start_bot()
