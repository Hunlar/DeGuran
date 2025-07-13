import logging
import asyncio
import json
import aiohttp
from datetime import datetime, timedelta

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackContext,
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- GLOBALS ---
GROUP_CHAT_ID = "@Cemaatsohbet"  # Bot mesaj gönderecek grup kullanıcı adı veya ID
SUPPORT_GROUP = "https://t.me/Kizilsancaktr"
ZEYD_BIN_SABR = "https://t.me/zeydbinhalit"
AYASOFYA_GIF_URL = "https://media.giphy.com/media/3o7TKtnuHOHHUjR38Y/giphy.gif"

HADISLER_JSON = "hadisler.json"  # Lokal hadis dosyası (aynı klasörde)

// Buraya API URL'leri:
SURELER_API = "https://api.acikkuran.com/v2/sureler"
AYET_API = "https://api.acikkuran.com/v2/ayetler"
EZAN_API_TEMPLATE = "https://api.aladhan.com/v1/timingsByCity?city={city}&country=Turkey&method=13"

# -- AYET ARAMA FONKSİYONLARI ---
async def fetch_json(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

async def ayet_bul(query: str):
    # Ayet ve sure isimleri türkçe arama yapıyor
    # API'nin verisi değişirse burası güncellenmeli
    try:
        # Önce sureleri çekelim, sonra arama yapalım
        sureler_resp = await fetch_json(SURELER_API)
        sureler = sureler_resp.get("data", [])
        # Sure isimlerinde query ile eşleşenleri bul
        eslesen_sureler = [s for s in sureler if query.lower() in s['name'].lower()]
        if not eslesen_sureler:
            return None
        # İlk eşleşen s 
        sure_id = eslesen_sureler[0]['id']

        # O suredeki ayetleri çek
        ayetler_resp = await fetch_json(f"{AYET_API}?sureId={sure_id}")
        ayetler = ayetler_resp.get("data", [])

        # Eğer query sayısal ise ayet no'yu da filtrele
        if query.isdigit():
            ayet_no = int(query)
            ayet = next((a for a in ayetler if a['verse'] == ayet_no), None)
            if ayet:
                return ayet
        # Sadece sure ismine göre ilk ayeti dönebiliriz
        if ayetler:
            return ayetler[0]
    except Exception as e:
        logger.error(f"Ayet arama hatası: {e}")
    return None

# --- HADİS GETİRME ---
def hadis_oku():
    try:
        with open(HADISLER_JSON, "r", encoding="utf-8") as f:
            hadisler = json.load(f)
        return hadisler
    except Exception as e:
        logger.error(f"Hadis dosyası okunamadı: {e}")
        return []

# --- KOMUTLAR ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [InlineKeyboardButton("Destek Grubu", url=SUPPORT_GROUP)],
        [InlineKeyboardButton("ZEYD BİN SABR", url=ZEYD_BIN_SABR)]
    ]
    await update.message.reply_animation(
        animation=AYASOFYA_GIF_URL,
        caption=(
            "Bu bot hayatın yoğun temposuna Kur'an-ı Kerim'i ve İslamiyeti hatırlatmak ve yaymak amacıyla yapılmıştır."
        ),
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def ara(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("Lütfen bir ayet veya sure ismi yazınız. Örnek: /ara Fatiha")
        return

    query = " ".join(context.args)
    ayet = await ayet_bul(query)
    if ayet:
        mesaj = f"**Ayet {ayet.get('verse')}:**\n{ayet.get('text')}\n\n**Meal:**\n{ayet.get('translation')}"
    else:
        mesaj = "Aradığınız ayet veya sure bulunamadı."

    await update.message.reply_text(mesaj, parse_mode='Markdown')

async def ayet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Rastgele ayet gönder
    try:
        ayetler_resp = await fetch_json(AYET_API)
        ayetler = ayetler_resp.get("data", [])
        if not ayetler:
            await update.message.reply_text("Ayet bilgisi alınamadı.")
            return
        import random
        ayet = random.choice(ayetler)
        mesaj = f"**Ayet {ayet.get('verse')} ({ayet.get('sureName')}):**\n{ayet.get('text')}\n\n**Meal:**\n{ayet.get('translation')}"
        await update.message.reply_text(mesaj, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Ayet komutu hata: {e}")
        await update.message.reply_text("Bir hata oluştu.")

async def hadis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hadisler = hadis_oku()
    if not hadisler:
        await update.message.reply_text("Hadis bilgisi alınamadı.")
        return
    import random
    secilen = random.choice(hadisler)
    mesaj = f"📜 **Hadis:**\n{secilen['text']}\n\n📚 **Kaynak:** {secilen['source']}"
    await update.message.reply_text(mesaj, parse_mode='Markdown')

async def ezan_vakti_gonder(context: CallbackContext):
    city = "Istanbul"  # İstersen bunu dinamik yapabiliriz
    try:
        url = EZAN_API_TEMPLATE.format(city=city)
        data = await fetch_json(url)
        if data.get("code") == 200:
            timings = data["data"]["timings"]
            now = datetime.now()
            for vakit in ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]:
                vakit_time_str = timings.get(vakit)
                if not vakit_time_str:
                    continue
                vakit_time = datetime.strptime(vakit_time_str, "%H:%M")
                # Ezan vakti gelince mesaj gönder (şu anki saat ile karşılaştır)
                if now.hour == vakit_time.hour and now.minute == vakit_time.minute:
                    mesaj = f"{city} için {vakit} namaz vakti geldi."
                    await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=mesaj)
    except Exception as e:
        logger.error(f"Ezan vakti kontrol hatası: {e}")

async def hourly_ayet_gonder(context: CallbackContext):
    # Her saat başı rastgele ayet gönder
    try:
        ayetler_resp = await fetch_json(AYET_API)
        ayetler = ayetler_resp.get("data", [])
        if not ayetler:
            return
        import random
        ayet = random.choice(ayetler)
        mesaj = f"**Saatlik Ayet:**\n{ayet.get('text')}\n\n**Meal:**\n{ayet.get('translation')}"
        await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=mesaj, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Saatlik ayet gönderme hatası: {e}")

def main():
    app = ApplicationBuilder().token("YOUR_BOT_TOKEN_HERE").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ara", ara))
    app.add_handler(CommandHandler("ayet", ayet))
    app.add_handler(CommandHandler("hadis", hadis))

    # Saatlik ayet gönderimi için job queue
    job_queue = app.job_queue
    job_queue.run_repeating(hourly_ayet_gonder, interval=3600, first=0)
    job_queue.run_repeating(ezan_vakti_gonder, interval=60, first=0)

    app.run_polling()

if __name__ == "__main__":
    main()
