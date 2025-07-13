import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Loglama
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Türkçe sure isimleri ve numaraları (tam listeyi daha sonra genişletebilirsin)
TURKCE_SURELER = {
    "fatiha": 1,
    "bakara": 2,
    "ali imran": 3,
    "nisâ": 4,
    "nisa": 4,
    "maide": 5,
    "enam": 6,
    "araf": 7,
    "anfal": 8,
    "tevbe": 9,
    "yunus": 10,
    "hud": 11,
    "yusuf": 12,
    "rad": 13,
    "ibrahim": 14,
    "hicr": 15,
    "nisan": 16,
    "nahl": 16,
    "isra": 17,
    "kehf": 18,
    "meryem": 19,
    "taha": 20,
    "enbiya": 21,
    "hacc": 22,
    "muminun": 23,
    "nur": 24,
    "furkan": 25,
    "saffat": 37,
    "zümer": 39,
    "mümin": 40,
    "fusilet": 41,
    "şura": 42,
    "zariyat": 51,
    "hucurat": 49,
    "duhan": 44,
    "caasiyah": 45,
    "ahkaf": 46,
    "muhammed": 47,
    "feth": 48,
    "hucurat": 49,
    "kaf": 50,
    "zariyat": 51,
    "tur": 52,
    "necâd": 53,
    "kamer": 54,
    "rahman": 55,
    "vasl": 56,
    "hadid": 57,
    "mücadele": 58,
    "haşr": 59,
    "mümtehine": 60,
    "saff": 61,
    "cuma": 62,
    "münâfikun": 63,
    "tevbe": 9,
    "nasr": 110,
    "masad": 111,
    "ikhlas": 112,
    "felak": 113,
    "nas": 114,
    # Gerekirse tamamını ekleyebilirim
}

# Ayet sayısı bilgisi (daha sağlıklı olması için)
SURE_AYET_SAYISI = {
    1: 7,
    2: 286,
    3: 200,
    4: 176,
    5: 120,
    6: 165,
    7: 206,
    8: 75,
    9: 129,
    10: 109,
    11: 123,
    12: 111,
    13: 43,
    14: 52,
    15: 99,
    16: 128,
    17: 111,
    18: 110,
    19: 98,
    20: 135,
    # Gerekirse genişlet
}

API_BASE = "https://api.alquran.cloud/v1"

def sure_no_bul(sure_adi: str):
    sure_adi = sure_adi.lower().strip()
    return TURKCE_SURELER.get(sure_adi)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📌 Destek Grubu", url="https://t.me/Kizilsancaktr")],
        [InlineKeyboardButton("📖 ZEYD BİN SABR", url="https://t.me/zeydbinhalit")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    photo_url = "https://i.imgur.com/0rLZClF.jpg"  # Doğrudan fotoğraf linki
    await update.message.reply_photo(
        photo=photo_url,
        caption=(
            "📖 *Kur'an-ı Kerim Botu*\n\n"
            "Bu bot, hayatın yoğun temposunda sana Kur’an’ı ve İslam’ı hatırlatmak için hazırlandı.\n"
            "Komutlar:\n"
            "/ara {sure veya ayet ismi} - Arapça ve Türkçe meal arama\n"
            "/ayet - Rastgele ayet gönderir\n"
            "/hadis - Rastgele hadis gönderir"
        ),
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def ara(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Lütfen aramak istediğiniz ayet veya sure adını yazınız. Örnek: /ara fatiha 1")
        return

    query = " ".join(context.args).lower()

    # Eğer örnek: "fatiha 1" gibiyse ayet numarası var mı kontrol et
    parts = query.split()
    sure_adi = parts[0]
    ayet_no = 1

    if len(parts) > 1 and parts[1].isdigit():
        ayet_no = int(parts[1])

    sure_no = sure_no_bul(sure_adi)
    if sure_no is None:
        await update.message.reply_text("Bu isimde bir sure bulunamadı. Lütfen Türkçe sure adını kontrol edin.")
        return

    max_ayet = SURE_AYET_SAYISI.get(sure_no, 150)
    if ayet_no > max_ayet or ayet_no < 1:
        await update.message.reply_text(f"Bu surede {max_ayet} ayetten fazla ayet yok.")
        return

    # API çağrıları
    try:
        arapca_url = f"{API_BASE}/ayah/{sure_no}:{ayet_no}/ar.alafasy"
        turkce_url = f"{API_BASE}/ayah/{sure_no}:{ayet_no}/tr.tr"

        arapca_response = requests.get(arapca_url)
        turkce_response = requests.get(turkce_url)

        if arapca_response.status_code != 200 or turkce_response.status_code != 200:
            await update.message.reply_text("API'den veri alınırken hata oluştu.")
            return

        arapca_text = arapca_response.json()["data"]["text"]
        turkce_text = turkce_response.json()["data"]["text"]

        mesaj = f"🕋 *{sure_adi.title()} {ayet_no}. Ayet*\n\n"
        mesaj += f"🇸🇦 {arapca_text}\n\n"
        mesaj += f"🇹🇷 {turkce_text}"

        await update.message.reply_text(mesaj, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Hata: {e}")
        await update.message.reply_text("Bir hata oluştu, lütfen daha sonra tekrar deneyin.")

import random

async def ayet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Rastgele sure ve ayet seç
    sure_no = random.choice(list(SURE_AYET_SAYISI.keys()))
    max_ayet = SURE_AYET_SAYISI[sure_no]
    ayet_no = random.randint(1, max_ayet)

    try:
        arapca_url = f"{API_BASE}/ayah/{sure_no}:{ayet_no}/ar.alafasy"
        turkce_url = f"{API_BASE}/ayah/{sure_no}:{ayet_no}/tr.tr"

        arapca_response = requests.get(arapca_url)
        turkce_response = requests.get(turkce_url)

        if arapca_response.status_code != 200 or turkce_response.status_code != 200:
            await update.message.reply_text("API'den veri alınırken hata oluştu.")
            return

        arapca_text = arapca_response.json()["data"]["text"]
        turkce_text = turkce_response.json()["data"]["text"]

        mesaj = f"🕋 *Rastgele Ayet*\n\n"
        mesaj += f"🇸🇦 {arapca_text}\n\n"
        mesaj += f"🇹🇷 {turkce_text}"

        await update.message.reply_text(mesaj, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Hata: {e}")
        await update.message.reply_text("Bir hata oluştu, lütfen daha sonra tekrar deneyin.")

# --- HADİS KOMUTU (Ali Hadis API) ---

async def hadis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        response = requests.get("https://api.sutanlab.id/hadith/random")
        if response.status_code != 200:
            await update.message.reply_text("Hadis API'sine erişilemiyor.")
            return
        data = response.json()
        hadis_metni = data.get("data", {}).get("text")
        kaynak = data.get("data", {}).get("reference")

        if hadis_metni and kaynak:
            mesaj = f"📜 *Rastgele Hadis*\n\n{hadis_metni}\n\n📖 Kaynak: {kaynak}"
            await update.message.reply_text(mesaj, parse_mode="Markdown")
        else:
            await update.message.reply_text("Hadis bulunamadı.")
    except Exception as e:
        logger.error(f"Hadis hatası: {e}")
        await update.message.reply_text("Hadis API'sinden veri alınırken hata oluştu.")

# Bot tokenı env değişkeninden al
TOKEN = os.getenv("TOKEN")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ara", ara))
    app.add_handler(CommandHandler("ayet", ayet))
    app.add_handler(CommandHandler("hadis", hadis))

    print("Bot başladı...")
    app.run_polling()

if __name__ == "__main__":
    main()
