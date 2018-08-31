"""Config values for archivebot."""


class Config:
    """Config class for convenient configuration."""

    # Get your telegram api-key from @botfather
    TELEGRAM_BOT_API_KEY = None

    # Get client api keys from https://my.telegram.org
    TELEGRAM_APP_API_ID = None
    TELEGRAM_APP_API_HASH = None

    SQL_URI = 'sqlite:///archivebot.db'
    TARGET_DIR = '/home/bot/archivebot/'

    # Can be omitted.
    # Only needed, if you want to monitor your bot in production with sentry.
    SENTRY_KEY = None

    # Allowed media types
    ALLOWED_MEDIA_TYPES = ['photo', 'document']


config = Config()
