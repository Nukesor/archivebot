"""A bot which downloads various files from chats."""
import os
import asyncio
import traceback
from telethon import TelegramClient, events
from telethon import types

from archivebot.config import config
from archivebot.db import get_session
from archivebot.subscriber import Subscriber
from archivebot.file import File
from archivebot.sentry import sentry
from archivebot.helper import (
    help_text,
    get_file_path,
    get_group_path,
)

NAME = config.TELEGRAM_BOT_API_KEY.split(':')[0]
archive = TelegramClient(NAME, config.TELEGRAM_APP_API_ID, config.TELEGRAM_APP_API_HASH)

# Ensure save directory for files exists
if not os.path.exists(config.TARGET_DIR):
    os.mkdir(config.TARGET_DIR)


async def help(bot, update):
    """Send a help text."""
    bot.sendMessage(chat_id=update.message.chat_id, text=help_text)


@archive.on(events.NewMessage(pattern='/set_name .'))
async def set_name(event):
    """Set query attributes."""
    session = get_session()
    try:
        chat_id = event.message.to_id.user_id
        group_name = event.message.message.split(' ', maxsplit=1)[1]
        subscriber = Subscriber.get_or_create(session, chat_id, group_name)

        old_group_path = get_group_path(subscriber.group_name)
        new_group_path = get_group_path(group_name)
        if os.path.exists(old_group_path) and old_group_path != new_group_path:
            os.rename(old_group_path, new_group_path)

        subscriber.group_name = group_name

        session.commit()

    except BaseException:
        traceback.print_exc()
        sentry.captureException()
    finally:
        session.remove()


@archive.on(events.NewMessage(pattern='/start'))
async def start(event):
    """Start the bot."""
    session = get_session()
    try:
        chat_id = event.message.to_id.user_id

        subscriber = Subscriber.get_or_create(session, chat_id, chat_id)
        subscriber.active = True
        session.add(subscriber)
        session.commit()

        text = 'Files posted in this channel will now be archived.'
        await asyncio.wait([event.respond(text)])
    except BaseException:
        traceback.print_exc()
        sentry.captureException()
    finally:
        session.remove()


@archive.on(events.NewMessage(pattern='/stop'))
async def stop(event):
    """Stop the bot."""
    session = get_session()
    try:
        chat_id = event.message.to_id.user_id

        subscriber = Subscriber.get_or_create(session, chat_id, chat_id)
        subscriber.active = False
        session.add(subscriber)
        session.commit()

        text = "Files won't be archived any longer."
        await asyncio.wait([event.respond(text)])
    except BaseException:
        traceback.print_exc()
        sentry.captureException()
    finally:
        session.remove()


@archive.on(events.NewMessage())
async def process(event):
    """Check if we received any files."""
    try:
        session = get_session()
        message = event.message
        chat_id = message.to_id.user_id
        subscriber = Subscriber.get_or_create(session, chat_id, chat_id)

        # Check if we should accept this message
        if not accept_message(subscriber, message):
            return

        # Check if we got a allowed media type
        file_type = None
        if 'photo' in config.ALLOWED_MEDIA_TYPES \
                and message.photo is not None:
            file_type = 'photo'
            file_id = message.photo.id

        if 'document' in config.ALLOWED_MEDIA_TYPES \
                and message.document is not None:
            file_type = 'document'
            file_id = message.document.id
        if not file_type:
            return

        # We only want messages from users
        user = await archive.get_entity(message.from_id)
        if not isinstance(user, types.User):
            return

        # Get and create paths for this file
        file_path, file_name = get_file_path(subscriber, user, message)

        if not os.path.isdir(file_path) and os.path.exists(file_path):
            sentry.captureMessage(
                "File already exists",
                extra={
                    'file_path': file_path,
                    'group': subscriber.group_name,
                    'user': user.username,
                },
                tags={'level': 'info'},
            )
            return

        # Create new file
        new_file = File(
            file_id,
            chat_id,
            message.id,
            user.id,
            file_name,
            file_type,
        )
        session.add(new_file)
        session.commit()

        # Download the file
        if file_path:
            success = await message.download_media(file_path)
        else:
            success = await message.download_media()

        # Download succeeded, if the result is not None
        if success is not None:
            # Mark the file as succeeded
            new_file.success = True
        session.commit()
    except Exception:
        traceback.print_exc()
        sentry.captureException()
    finally:
        session.remove()


def accept_message(subscriber, message):
    """Check if we should accept this message."""
    if subscriber.active is False:
        return False

    # No media => not interesting
    if message.media is None:
        return False

    return True


archive.start(bot_token=config.TELEGRAM_BOT_API_KEY)
