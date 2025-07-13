import os
import json
import random
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Destek Grubu", url="https://t.me/Kizilsancaktr")],
        [InlineKeyboardButton("ZEYD BİN SABR", url="https://t.me/zeydbinhalit")]
    ]
    await update.message.reply_photo(
        photo="https://i.imgur.com/3VJNx7B.jpg",  # Ayasofya görseli düzgün çalışıyor
        caption=(
            "Bu bot, hayatın yoğun temposunda Kur’an-ı Kerim’i ve İslam’ı hatırlatmak için yapılmıştır."
        ),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def get_meal(sure_id, ayet_no):
    url = f"https://api.acikkuran.com/v2/ayetler?sure_id={sure_id}&ayet_no={ayet_no}"
    res = requests.get(url)
    if res.status_code != 200:
        return "❌ Ayet bulunamadı."
    data = res.json()["data"][0]
    return f"*{data['sure']} Suresi {data['ayet_no']}. Ayet*\n\n📖 {data['ayet']}\n\n🇹🇷 {data['meal']}"

async def ayet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = requests.get("https://api.acikkuran.com/v2/ayetler?limit=1&random=true").json()
    ayet = response["data"][0]
    mesaj = f"*{ayet['sure']} Suresi {ayet['ayet_no']}. Ayet*\n\n📖 {ayet['ayet']}\n\n🇹🇷 {ayet['meal']}"
    await update.message.reply_text(mesaj, parse_mode=ParseMode.MARKDOWN)

async def ara(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Kullanım: /ara {sure adı} [ayet no (isteğe bağlı)]")
        return

    if len(args) >= 2 and args[1].isdigit():
        sure_adi = args[0].lower()
        ayet_no = int(args[1])
        sureler = requests.get("https://api.acikkuran.com/v2/sureler").json()
        for s in sureler["data"]:
            if sure_adi in [s["adi"].lower(), s["adi_latin"].lower()]:
                sure_id = s["id"]
                mesaj = get_meal(sure_id, ayet_no)
                await update.message.reply_text(mesaj, parse_mode=ParseMode.MARKDOWN)
                return
        await update.message.reply_text("❌ Böyle bir sure bulunamadı.")
        return

    sure_adi = " ".join(args).lower()
    sureler = requests.get("https://api.acikkuran.com/v2/sureler").json()
    for s in sureler["data"]:
        if sure_adi in [s["adi"].lower(), s["adi_latin"].lower()]:
            sure_id = s["id"]
            response = requests.get(f"https://api.acikkuran.com/v2/ayetler?sure_id={sure_id}&limit=3").json()
            mesajlar = []
            for ayet in response["data"]:
                mesajlar.append(
                    f"*{ayet['sure']} Suresi {ayet['ayet_no']}. Ayet*\n\n📖 {ayet['ayet']}\n\n🇹🇷 {ayet['meal']}"
                )
            await update.message.reply_text("\n\n".join(mesajlar), parse_mode=ParseMode.MARKDOWN)
            return

    await update.message.reply_text("❌ Böyle bir sure bulunamadı.")

async def hadis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open("hadisler.json", "r", encoding="utf-8") as f:
            hadisler = json.load(f)
        hadis = random.choice(hadisler)
        mesaj = f"*Hadis-i Şerif*\n\n📜 {hadis['text']}\n\n📚 {hadis['source']}"
        await update.message.reply_text(mesaj, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await update.message.reply_text("❌ Hadisler yüklenemedi.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ayet", ayet))
    app.add_handler(CommandHandler("ara", ara))
    app.add_handler(CommandHandler("hadis", hadis))
    print("Bot çalışıyor...")
    app.run_polling()
