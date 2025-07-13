import os
import random
import requests
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
)

TOKEN = os.getenv("TOKEN")  # Heroku'ya TOKEN olarak eklendiğini varsayıyoruz

# /start komutu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_url = "https://upload.wikimedia.org/wikipedia/commons/6/6d/Ayasofya2020.jpg"

    keyboard = [
        [InlineKeyboardButton("📌 Destek Grubu", url="https://t.me/Kizilsancaktr")],
        [InlineKeyboardButton("📖 ZEYD BİN SABR", url="https://t.me/zeydbinhalit")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await update.message.reply_photo(
            photo=photo_url,
            caption=(
                "📖 *Kur'an-ı Kerim Botu*\n\n"
                "Bu bot, hayatın yoğun temposunda sana Kur’an’ı ve İslam’ı hatırlatmak için hazırlandı.\n"
                "Her saat başı rastgele ayet gönderir. Komutları kullanarak da erişim sağlayabilirsin."
            ),
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text("Görsel gönderilemedi. Bot çalışıyor.\n" + str(e))

# /ayet komutu
def get_random_ayah():
    ayah_number = random.randint(1, 6236)

    arabic_url = f"https://api.alquran.cloud/v1/ayah/{ayah_number}"
    turkish_url = f"https://api.alquran.cloud/v1/ayah/{ayah_number}/tr.duz"

    try:
        arabic_response = requests.get(arabic_url).json()
        turkish_response = requests.get(turkish_url).json()

        if arabic_response["status"] == "OK" and turkish_response["status"] == "OK":
            surah = arabic_response["data"]["surah"]["name"]
            num = arabic_response["data"]["numberInSurah"]
            arabic = arabic_response["data"]["text"]
            turkish = turkish_response["data"].get("text", "❗Türkçe meal bulunamadı.")

            return (
                f"📖 *{surah} Suresi {num}. Ayet*\n\n"
                f"🔹 _{arabic}_\n\n"
                f"💬 {turkish}"
            )
        else:
            return "⚠️ Ayet verisi alınamadı."
    except Exception as e:
        print("Ayet alma hatası:", e)
        return "⚠️ Ayet çekilirken hata oluştu."

async def ayet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mesaj = get_random_ayah()
    await update.message.reply_text(mesaj, parse_mode="Markdown")

# /hadis komutu
async def hadis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        kaynak = "muslim"
        url = f"https://api.sutanlab.id/hadith/{kaynak}"

        response = requests.get(url)
        data = response.json()

        if data["status"] != "OK":
            await update.message.reply_text("❌ Hadis listesi alınamadı.")
            return

        total = data["data"]["available"]
        num = random.randint(1, total)

        hadis_url = f"https://api.sutanlab.id/hadith/{kaynak}/{num}"
        hadis_response = requests.get(hadis_url).json()

        if hadis_response["status"] != "OK":
            await update.message.reply_text("❌ Hadis getirilemedi.")
            return

        hadis = hadis_response["data"]
        metin = hadis.get("arab") or hadis.get("id") or "Hadis metni yok."
        kaynak_bilgi = f"{hadis['name']}, No: {hadis['number']}"

        await update.message.reply_text(f"📜 \"{metin}\"\n\n📚 {kaynak_bilgi}")
    except Exception as e:
        print("Hadis hatası:", e)
        await update.message.reply_text("⚠️ Hadis verisi alınırken hata oluştu.")

# /ara komutu
async def ara(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❓ Lütfen bir ayet veya sure ismi yazınız.")
        return

    query = " ".join(context.args)
    search_url = f"https://api.alquran.cloud/v1/search/{query}/all/tr.duz"

    try:
        response = requests.get(search_url).json()
        if response["status"] == "OK" and response["data"]["count"] > 0:
            results = response["data"]["matches"][:3]
            msg = ""
            for r in results:
                surah = r["surah"]["name"]
                number = r["numberInSurah"]
                text = r["text"]
                msg += f"📖 *{surah}* {number}. Ayet\n{text}\n\n"
            await update.message.reply_text(msg, parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ Uygun sonuç bulunamadı.")
    except Exception as e:
        print("Arama hatası:", e)
        await update.message.reply_text("⚠️ Arama sırasında hata oluştu.")

# Ana çalıştırıcı
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ayet", ayet))
    app.add_handler(CommandHandler("hadis", hadis))
    app.add_handler(CommandHandler("ara", ara))

    print("🤖 Bot başlatılıyor...")
    app.run_polling()

if __name__ == "__main__":
    main()
