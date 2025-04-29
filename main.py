import time
import feedparser
from googletrans import Translator
from telegram import Bot
from telegram.error import TelegramError
import logging
import re
from html import unescape
from bs4 import BeautifulSoup

# === CONFIGURATION ===
TELEGRAM_TOKEN = "8036416560:AAETLYeBRZe8w0bfpJujLNnJgG--kJqnsK8"
TELEGRAM_CHAT_ID = "5249034734"
RSS_FEED_URL = "https://rss.app/feeds/2eXUg2P9zvxO6Hym.xml"
CHECK_INTERVAL = 30  # vérifie toutes les 30 secondes

# === INITIALISATION ===
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
            logger.info("Aucun article trouvé.")
            return None
        return feed.entries[0]
    except Exception as e:
        logger.error(f"Erreur lors du parsing RSS : {str(e)}")
        return None

def extract_image(summary_html):
    try:
        matches = re.findall(r'<img[^>]+src="([^"]+)"', summary_html)
        for url in matches:
            if any(url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                return url
        return None
    except Exception as e:
        logger.warning(f"Erreur extraction image : {str(e)}")
        return None

def clean_html(html_text):
    try:
        soup = BeautifulSoup(html_text, 'html.parser')
        return unescape(soup.get_text().strip())
    except Exception:
        return html_text  # en cas d'erreur, retourner brut

def process_entry(entry):
    global last_entry_id

    entry_id = entry.get('id', entry.link)
    if entry_id == last_entry_id:
        return False

    try:
        title_fr = translator.translate(entry.title, dest='fr').text
        summary = clean_html(entry.get('summary', ''))
        summary_fr = translator.translate(summary, dest='fr').text if summary else ""

        image_url = extract_image(entry.get('summary', ''))

        message = (
            f"*{title_fr}*\n"
            f"{summary_fr}\n\n"
            f"🔗 [Lire l’article original]({entry.link})"
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

        logger.info(f"✅ Article publié : {title_fr[:60]}...")
        last_entry_id = entry_id
        return True

    except TelegramError as te:
        logger.error(f"Erreur Telegram : {str(te)}")
    except Exception as e:
        logger.error(f"Erreur traitement article : {str(e)}")
    return False

def main_loop():
    logger.info("🤖 Bot démarré. Vérifications toutes les 30 secondes.")
    while True:
        try:
            start_time = time.time()
            entry = fetch_latest_entry()
            if entry:
                process_entry(entry)
            elapsed = time.time() - start_time
            time.sleep(max(0, CHECK_INTERVAL - elapsed))
        except KeyboardInterrupt:
            logger.info("⛔ Bot arrêté manuellement.")
            break
        except Exception as e:
            logger.critical(f"Erreur critique : {str(e)}")
            time.sleep(60)

if __name__ == "__main__":
    main_loop()
