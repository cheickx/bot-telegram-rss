import os
import time
import feedparser
import requests
from bs4 import BeautifulSoup
from googletrans import Translator
from telegram import Bot
from telegram.error import TelegramError

# === CONFIGURATION ===
TELEGRAM_TOKEN = "8036416560:AAETLYeBRZe8w0bfpJujLNnJgG--kJqnsK8"
TELEGRAM_CHAT_ID = "5249034734"
RSS_FEED_URL = "https://rss.app/feeds/2eXUg2P9zvxO6Hym.xml"
CHECK_INTERVAL = 30  # toutes les 30 secondes

# === INITIALISATION ===
bot = Bot(token=TELEGRAM_TOKEN)
translator = Translator(service_urls=['translate.google.com'])
last_entry_id = None

def fetch_latest_entry():
    feed = feedparser.parse(RSS_FEED_URL)
    if not feed.entries:
        return None
    return feed.entries[0]

def extract_image_url(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    img_tag = soup.find('img')
    return img_tag['src'] if img_tag and 'src' in img_tag.attrs else None

def process_entry(entry):
    global last_entry_id
    entry_id = entry.get('id', entry.link)
    if entry_id == last_entry_id:
        return False

    title = entry.title
    summary = entry.get('summary', '')
    link = entry.link

    # Traduction
    title_fr = translator.translate(title, dest='fr').text
    summary_fr = translator.translate(summary, dest='fr').text if summary else ""
    
    # Image
    image_url = extract_image_url(summary)

    # Construction du message
    if summary_fr != title_fr and summary_fr.strip():
        message = f"✨ NOUVEL ARTICLE ✨\n\n📌 {title_fr}\n\n📝 {summary_fr}\n\n🔗 [Lire l’article original]({link})"
    else:
        message = f"✨ NOUVEL ARTICLE ✨\n\n📌 {title_fr}\n\n🔗 [Lire l’article original]({link})"

    # Envoi du message
    try:
        if image_url:
            bot.send_photo(
                chat_id=TELEGRAM_CHAT_ID,
                photo=image_url,
                caption=message,
                parse_mode='Markdown'
            )
        else:
            bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=message,
                parse_mode='Markdown'
            )
        last_entry_id = entry_id
        return True
    except TelegramError as e:
        print(f"Erreur d'envoi Telegram : {e}")
        return False

def main_loop():
    print("Bot RSS démarré. Vérification toutes les 30 secondes.")
    while True:
        try:
            entry = fetch_latest_entry()
            if entry:
                process_entry(entry)
        except Exception as e:
            print(f"Erreur : {e}")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main_loop()
