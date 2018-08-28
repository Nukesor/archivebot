"""The actual bot."""

import os
import traceback
from telethon import TelegramClient, sync  # noqa
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    Updater,
)

from archivebot.config import config
from archivebot.db import get_session
from archivebot.subscriber import Subscriber
from archivebot.file import File
from archivebot.sentry import Sentry
from archivebot.helper import help_text


class ArchiveBot():
    """A bot which checks if there is a new record in the server section of archive."""

    def __init__(self):
        """Initialize telegram bot and all needed variables."""
        # Initialize sentry
        self.sentry = Sentry()
        self.telegram_client = TelegramClient(
            'archiveBot',
            config.TELEGRAM_APP_API_ID,
            config.TELEGRAM_APP_API_HASH,
        )
        self.telegram_client.connect()

        # Save directory for files
        if not os.path.exists(config.TARGET_DIR):
            os.mkdir(config.TARGET_DIR)

        # Telegram logic updater and dispatcher
        self.updater = Updater(token=config.TELEGRAM_BOT_API_KEY)
        dispatcher = self.updater.dispatcher

        self.check_telegram_client_login(self.updater.bot)

        # Create handler
        message_handler = MessageHandler(config.MESSAGE_FILTER, self.process)
        help_handler = CommandHandler('help', self.help)
        start_handler = CommandHandler('start', self.start)
        stop_handler = CommandHandler('stop', self.stop)
        set_name_handler = CommandHandler('set_name', self.set_name)
        login = CommandHandler('login', self.login)

        # Add handler
        dispatcher.add_handler(message_handler)
        dispatcher.add_handler(help_handler)
        dispatcher.add_handler(start_handler)
        dispatcher.add_handler(stop_handler)
        dispatcher.add_handler(set_name_handler)
        dispatcher.add_handler(login)

        self.updater.start_polling()

    def main(self):
        """Update loop of the bot."""
        self.updater.idle()

    def help(self, bot, update):
        """Send a help text."""
        bot.sendMessage(chat_id=update.message.chat_id, text=help_text)

    def login(self, bot, update):
        """Set query attributes."""
        try:
            login_code = update.message.text.split(' ', maxsplit=1)[1].strip()[:-3]
            self.telegram_client.sign_in(config.TELEGRAM_PHONE_NUMBER, login_code)
            bot.sendMessage(
                config.TELEGRAM_ADMIN_USER_ID,
                "Login successful",
            )
        except BaseException:
            traceback.print_exc()
            self.sentry.captureException()

    def set_name(self, bot, update):
        """Set query attributes."""
        session = get_session()
        try:
            chat_id = update.message.chat_id
            group_name = update.message.text.split(' ', maxsplit=1)[1]
            subscriber = Subscriber.get_or_create(session, chat_id, group_name)

            old_group_path = self.get_group_path(subscriber.group_name)
            new_group_path = self.get_group_path(group_name)
            if old_group_path != new_group_path:
                os.rename(old_group_path, new_group_path)

            subscriber.group_name = group_name

            session.commit()

        except BaseException:
            traceback.print_exc()
            self.sentry.captureException()
        finally:
            session.remove()

    def start(self, bot, update):
        """Start the bot."""
        session = get_session()
        try:
            chat_id = update.message.chat_id

            subscriber = Subscriber.get_or_create(session, chat_id, chat_id)
            subscriber.active = True
            session.add(subscriber)
            session.commit()

            text = 'Files posted in this channel will now be archived.'
            bot.sendMessage(chat_id=chat_id, text=text)
        except BaseException:
            traceback.print_exc()
            self.sentry.captureException()
        finally:
            session.remove()

    def stop(self, bot, update):
        """Stop the bot."""
        session = get_session()
        try:
            chat_id = update.message.chat_id

            subscriber = Subscriber.get_or_create(session, chat_id, chat_id)
            subscriber.active = False
            session.add(subscriber)
            session.commit()

            text = "Files won't be archived any longer."
            bot.sendMessage(chat_id=chat_id, text=text)
        except BaseException:
            traceback.print_exc()
            self.sentry.captureException()
        finally:
            session.remove()

    def process(self, bot, update):
        """Check if we received any files."""
        try:
            session = get_session()
            message = update.message
            chat_id = message.chat_id
            user = message.from_user
            subscriber = Subscriber.get_or_create(session, chat_id, chat_id)

            if subscriber.active is False:
                return

            if message.document is None:
                return

            # Get and create paths for this file
            file_path = self.get_file_path(subscriber, user, message)

            if os.path.exists(file_path):
                self.sentry.captureMessage(
                    "File already exists",
                    extra={
                        'file_path': file_path,
                        'group': subscriber.group_name,
                        'user': user.username,
                    },
                    tags={'level': 'info'},
                )
                return

            self.check_telegram_client_login(bot)

            print('Message')
            # Try to get the telegram client message
            client_message = self.telegram_client.get_messages(
                chat_id, ids=message.message_id)

            if client_message is None:
                print('No message')
                self.sentry.captureMessage(
                    "Message is not readable by client",
                    extra={
                        'group': subscriber.group_name,
                        'user': user.username,
                    },
                    tags={'level': 'info'},
                )
                return

            # Create new file
            new_file = File(
                message.document.file_id,
                chat_id,
                message.message_id,
                user.id,
                message.document.file_name,
            )
            session.add(new_file)
            session.commit()

            print('here')
            # Download the file
            success = self.telegram_client.download_media(client_message, file_path)
            print(success)

            # Download succeeded, if the result is not None
            if success is not None:
                # Mark the file as succeeded
                new_file.success = True
            session.commit()
        except Exception:
            traceback.print_exc()
            self.sentry.captureException()
        finally:
            session.remove()

    def get_group_path(self, group_name):
        """Compile the directory path for this group."""
        return os.path.join(config.TARGET_DIR, group_name)

    def get_file_path(self, subscriber, user, message):
        """Compile the file path and ensure the parent directories exist."""
        user_path = os.path.join(self.get_group_path(subscriber.group_name), user.username.lower())
        if not os.path.exists(user_path):
            os.makedirs(user_path, exist_ok=True)

        return os.path.join(user_path, message.document.file_name)

    def check_telegram_client_login(self, bot):
        """Check if we have a valid telegram login and request a new code via telegram chat or manual input."""
        if not self.telegram_client.is_user_authorized():
            self.telegram_client.send_code_request(config.TELEGRAM_PHONE_NUMBER)

            # We don't have a valid login. Await manual login or send notification.
            if not config.TELEGRAM_ADMIN_USER_ID:
                self.telegram_client.sign_in(
                    config.TELEGRAM_PHONE_NUMBER,
                    input('Enter code: '),
                )
            else:
                bot.sendMessage(
                    config.TELEGRAM_ADMIN_USER_ID,
                    "Expecting login code. Add three symbols (e.g. 34251XXX).",
                )
