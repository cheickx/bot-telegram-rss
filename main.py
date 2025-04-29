import os
import time
import feedparser
from googletrans import Translator
from telegram import Bot
from telegram.error import TelegramError
import logging

# Configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8036416560:AAETLYeBRZe8w0bfpJujLNnJgG--kJqnsK8")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "5249034734")
RSS_FEED_URL = os.getenv("RSS_FEED_URL", "https://rss.app/feeds/2eXUg2P9zvxO6Hym.xml")
CHECK_INTERVAL = 120  # 2 minutes

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
last_entry_id = None

def fetch_latest_entry():
    try:
        feed = feedparser.parse(RSS_FEED_URL)
        if not feed.entries:
            logger.info("Aucun article trouvé dans le flux")
            return None
        return feed.entries[0]
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du flux: {str(e)}")
        return None

def process_entry(entry):
    global last_entry_id
    
    entry_id = entry.get('id', entry.link)
    if entry_id == last_entry_id:
        logger.debug("Article déjà traité")
        return False

    try:
        title_fr = translator.translate(entry.title, dest='fr').text
        summary = entry.get('summary', '')
        summary_fr = translator.translate(summary, dest='fr').text if summary else "Pas de résumé disponible"

        message = (
            f"✨ **NOUVEL ARTICLE** ✨\n\n"
            f"📌 *{title_fr}*\n\n"
            f"📝 {summary_fr}\n\n"
            f"🔗 [Lire l'article original]({entry.link})"
        )

        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode='Markdown',
            disable_web_page_preview=False
        )
        
        logger.info(f"Nouvel article envoyé: {title_fr[:50]}...")
        last_entry_id = entry_id
        return True

    except Exception as e:
        logger.error(f"Erreur lors du traitement: {str(e)}")
        return False

def main_loop():
    logger.info("🤖 Bot RSS Dernier Article - En service")
    
    while True:
        try:
            start_time = time.time()
            
            if entry := fetch_latest_entry():
                process_entry(entry)
            
            elapsed = time.time() - start_time
            sleep_time = max(0, CHECK_INTERVAL - elapsed)
            time.sleep(sleep_time)
            
        except KeyboardInterrupt:
            logger.info("Arrêt manuel du bot")
            break
        except Exception as e:
            logger.critical(f"Erreur critique: {str(e)}")
            time.sleep(60)

if __name__ == "__main__":
    main_loop())
