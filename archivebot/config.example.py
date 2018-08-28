"""Config values for archivebot."""
from telegram.ext import Filters


class Config:
    """Config class for convenient configuration."""

    # Get your telegram api-key from @botfather
    TELEGRAM_BOT_API_KEY = None

    # Get client api keys from https://my.telegram.org
    TELEGRAM_APP_API_ID = None
    TELEGRAM_APP_API_HASH = None
    TELEGRAM_PHONE_NUMBER = None

    # The chat used for entering the login telegram login code
    TELEGRAM_ADMIN_USER_ID = None

    SQL_URI = 'sqlite:///archivebot.db'
    TARGET_DIR = '/home/bot/archivebot/'
    SENTRY_KEY = None
    # Allow videos and documents. Allow more file types with e.g. (.. | Filters.image)
    MESSAGE_FILTER = (Filters.document | Filters.video)


config = Config()
