"""Some static stuff or helper functions for archive bot."""
import os
import asyncio
import traceback
from telethon import types

from archivebot.db import get_session
from archivebot.sentry import sentry
from archivebot.config import config


possible_media = ['document', 'photo']

help_text = f"""A handy telegram bot which allows to store files on your server, which are posted in a chat.
For example, this is great to collect images and videos from all members of your last holiday trip or simply to push backups or interesting files from your telegram chats to your server.

If you forward messages from other chats and `sort_by_user` is on, the file will still be saved under the name of the original owner.

To send multiple uncompressed pictures and videos with your phone:
1. Click the share button
2. Select `File`
3. Select Gallery (To send images without compression)

Available commands:

/start Start the bot
/stop Stop the bot
/set_name Set the name for this chat. This also determines the name of the target folder on the server.
/verbose ['true', 'false'] The bot will notify if there are duplicate files or uncompressed images are not allowed.
/sort_by_user [true, false] Incoming files will be sorted by user in the server directory for this chat.
/accept {possible_media} Specify the allowed media types. Always provide a space separated list of all accepted media types, e.g. 'document photo'.
/info Show current settings.
/help Show this text
"""


def event_wrapper(func):
    """Wrap a telethon event to create a session and handle exceptions."""
    async def wrapper(event):
        session = get_session()
        try:
            await func(event, session)
        except BaseException:
            await asyncio.wait([event.respond("Some unknown error occurred.")])
            traceback.print_exc()
            sentry.captureException()
        finally:
            session.remove()
    return wrapper


def get_info_text(subscriber):
    """Format the info text."""
    return f"""Current settings:

Name: {subscriber.channel_name}
Active: {subscriber.active}
Accepted Media: {subscriber.accepted_media}
Verbose: {subscriber.verbose}
Sort files by User: {subscriber.sort_by_user}
"""


def get_channel_path(channel_name):
    """Compile the directory path for this channel."""
    return os.path.join(config.TARGET_DIR, channel_name)


def get_file_path(subscriber, username, media):
    """Compile the file path and ensure the parent directories exist."""
    # If we don't sort by user, use the channel_path
    if not subscriber.sort_by_user:
        directory = get_channel_path(subscriber.channel_name)
    # sort_by_user is active. Add the user directory.
    else:
        directory = os.path.join(
            get_channel_path(subscriber.channel_name),
            username.lower(),
        )

    # Create the directory
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

    # We have a document. Documents have a filename attribute.
    # Use this for choosing the exact file path.
    if media.document:
        for attribute in media.document.attributes:
            if isinstance(attribute, types.DocumentAttributeFilename):
                return (os.path.join(directory, attribute.file_name), attribute.file_name)

    # We have a photo. Photos have no file name, thereby return the directory
    # and let telethon decide the name of the file.
    return (directory, None)


def get_bool_from_text(text):
    """Check if we can convert this string to bool."""
    if text.lower() in ['1', 'true', 'on']:
        return True
    elif text.lower() in ['0', 'false', 'off']:
        return False
    else:
        raise Exception("Unknown boolean text")
