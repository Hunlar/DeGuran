import json
import os
import random
import requests
import schedule
import time
import threading
from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Ortam değişkeni
TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROUPS_FILE = "groups.json"

bot = Bot(token=TOKEN)

# Grup ID'si kaydet
def save_group(chat_id):
    try:
        with open(GROUPS_FILE, "r") as f:
            groups = json.load(f)
    except FileNotFoundError:
        groups = []

    if chat_id not in groups:
        groups.append(chat_id)
        with open(GROUPS_FILE, "w") as f:
            json.dump(groups, f)

# API'den ayet çek
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

# Tüm gruplara gönder
def send_to_all_groups():
    try:
        with open(GROUPS_FILE, "r") as f:
            groups = json.load(f)
    except FileNotFoundError:
        groups = []

    message = get_random_ayah()
    for chat_id in groups:
        try:
            bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
        except Exception as e:
            print(f"Hata: {e} - {chat_id}")

# Zamanlayıcı başlat
def start_scheduler():
    schedule.every().hour.at(":00").do(send_to_all_groups)
    while True:
        schedule.run_pending()
        time.sleep(1)

# Grup mesajı gelirse kaydet
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in ["group", "supergroup"]:
        save_group(update.effective_chat.id)

# Telegram listener başlat
def start_telegram_listener():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    app.run_polling()

# Başlat
threading.Thread(target=start_scheduler).start()
start_telegram_listener()
