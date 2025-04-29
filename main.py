import os
import time
import feedparser
from bs4 import BeautifulSoup
from googletrans import Translator
from telegram import Bot
from telegram.error import TelegramError
import logging
import requests

# Configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8036416560:AAETLYeBRZe8w0bfpJujLNnJgG--kJqnsK8")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "5249034734")
RSS_FEED_URL = os.getenv("RSS_FEED_URL", "https://rss.app/feeds/2eXUg2P9zvxO6Hym.xml")
CHECK_INTERVAL = 30  # en secondes

# Initialisation
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('rss_bot.log')
    ]
)
logger = logging.getLogger(__name__)
bot = Bot(token=TELEGRAM_TOKEN)
translator = Translator(service_urls=['translate.google.com'])

last_entry_id = None  # pour éviter les doublons

def extract_image(entry):
    """Récupère la première image du flux s'il y en a"""
    if "media_content" in entry:
        for media in entry.media_content:
            if 'url' in media:
                return media['url']
    elif "summary" in entry:
        soup = BeautifulSoup(entry.summary, 'html.parser')
        img_tag = soup.find("img")
        if img_tag and img_tag.get("src"):
            return img_tag["src"]
    return None

def fetch_latest_entry():
    try:
        feed = feedparser.parse(RSS_FEED_URL)
        if not feed.entries:
            logger.info("Aucun article trouvé.")
            return None
        return feed.entries[0]
    except Exception as e:
        logger.error(f"Erreur de récupération du flux : {e}")
        return None

def process_entry(entry):
    global last_entry_id

    entry_id = entry.get("id", entry.link)
    if entry_id == last_entry_id:
        return False

    try:
        # Nettoyage du résumé
        raw_summary = entry.get('summary', '')
        soup = BeautifulSoup(raw_summary, 'html.parser')
        clean_summary = soup.get_text().strip()

        # Retirer doublons
        if entry.title.strip() in clean_summary:
            clean_summary = clean_summary.replace(entry.title.strip(), "").strip()

        # Traduction
        title_fr = translator.translate(entry.title, dest="fr").text
        summary_fr = translator.translate(clean_summary, dest="fr").text if clean_summary else "Pas de résumé"

        # Message
        message = f"✨ NOUVEL ARTICLE ✨\n\n📌 *{title_fr}*\n\n📝 {summary_fr}\n\n🔗 [Lire l’article original]({entry.link})"

        # Envoi image + texte
        image_url = extract_image(entry)
        if image_url:
            bot.send_photo(
                chat_id=TELEGRAM_CHAT_ID,
                photo=image_url,
                caption=message,
                parse_mode="Markdown",
            )
        else:
            bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=message,
                parse_mode="Markdown",
                disable_web_page_preview=False,
            )

        logger.info(f"Article posté : {title_fr[:50]}...")
        last_entry_id = entry_id
        return True

    except TelegramError as e:
        logger.error(f"Erreur Telegram : {e}")
    except Exception as e:
        logger.error(f"Erreur générale : {e}")
    return False

def main_loop():
    logger.info("🤖 Bot RSS en cours d'exécution...")
    while True:
        try:
            start = time.time()
            entry = fetch_latest_entry()
            if entry:
                process_entry(entry)
            time.sleep(max(0, CHECK_INTERVAL - (time.time() - start)))
        except KeyboardInterrupt:
            logger.info("Arrêt du bot.")
            break
        except Exception as e:
            logger.critical(f"Erreur critique : {e}")
            time.sleep(60)

if __name__ == "__main__":
    main_loop()
