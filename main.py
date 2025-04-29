import time
import feedparser
from googletrans import Translator
from telegram import Bot
from telegram.error import TelegramError
import logging
import re

# === CONFIGURATION PERSONNELLE ===
TELEGRAM_TOKEN = "8036416560:AAETLYeBRZe8w0bfpJujLNnJgG--kJqnsK8"
TELEGRAM_CHAT_ID = "5249034734"
RSS_FEED_URL = "https://rss.app/feeds/2eXUg2P9zvxO6Hym.xml"
CHECK_INTERVAL = 120  # toutes les 2 minutes

# === LOGGING (utile pour débogage) ===
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
translator = Translator()
last_entry_id = None

def fetch_latest_entry():
    try:
        feed = feedparser.parse(RSS_FEED_URL)
        if not feed.entries:
            logger.info("Aucun article trouvé dans le flux.")
            return None
        return feed.entries[0]
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du flux : {str(e)}")
        return None

def extract_image(summary_html):
    match = re.search(r'<img[^>]+src="([^"]+)"', summary_html)
    if match:
        return match.group(1)
    return None

def process_entry(entry):
    global last_entry_id

    entry_id = entry.get('id', entry.link)
    if entry_id == last_entry_id:
        logger.debug("Article déjà traité.")
        return False

    try:
        title_fr = translator.translate(entry.title, dest='fr').text
        summary = entry.get('summary', '')
        summary_fr = translator.translate(summary, dest='fr').text if summary else "Pas de résumé disponible."

        image_url = extract_image(summary)

        message = (
            f"✨ *NOUVEL ARTICLE* ✨\n\n"
            f"📌 *{title_fr}*\n\n"
            f"📝 {summary_fr}\n\n"
            f"🔗 [Lire l'article original]({entry.link})"
        )

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
                parse_mode='Markdown',
                disable_web_page_preview=False
            )

        logger.info(f"✅ Article envoyé : {title_fr[:60]}...")
        last_entry_id = entry_id
        return True

    except TelegramError as te:
        logger.error(f"Erreur Telegram : {str(te)}")
    except Exception as e:
        logger.error(f"Erreur de traitement de l'article : {str(e)}")
    return False

def main_loop():
    logger.info("🤖 Bot en marche, vérifie toutes les 2 minutes...")
    while True:
        try:
            start_time = time.time()
            entry = fetch_latest_entry()
            if entry:
                process_entry(entry)
            elapsed = time.time() - start_time
            time.sleep(max(0, CHECK_INTERVAL - elapsed))
        except KeyboardInterrupt:
            logger.info("⛔ Arrêt manuel du bot.")
            break
        except Exception as e:
            logger.critical(f"Erreur critique : {str(e)}")
            time.sleep(60)

if __name__ == "__main__":
    main_loop()
