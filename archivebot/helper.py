"""Some static stuff or helper functions for archive bot."""
import os
from archivebot.config import config
from telethon import types


possible_media = ['document', 'photo']

help_text = f"""A handy telegram bot which allows to store files on your server, which are posted in a group chat or a normal chat.
For instance, this is great to collect images and videos from your last holiday trip or simply to push backups or interesting files from your telegram chats to your server.

If you forward messages from other chats, the file will still be saved under the name of the original owner

To send multiple uncompressed pictures and videos with your phone:
1. Click the share button
2. Select `File`
3. Select Gallery (To send images without compression)

Available commands:

/start Start the bot
/stop Stop the bot
/set_name Set the name for this chat. This also determines the name of the target folder on the server.
/verbose ['true', 'false'] The bot will notify if there are duplicate files or uncompressed images are not allowed.
/accept {possible_media} Specify the allowed media types. Always provide a space separated list of all accepted media types, e.g. 'document photo'.
/help Show this text
"""


def get_channel_path(channel_name):
    """Compile the directory path for this channel."""
    return os.path.join(config.TARGET_DIR, channel_name)


def get_file_path(subscriber, username, media):
    """Compile the file path and ensure the parent directories exist."""
    # Create user directory
    user_path = os.path.join(
        get_channel_path(subscriber.channel_name),
        username.lower(),
    )
    if not os.path.exists(user_path):
        os.makedirs(user_path, exist_ok=True)

    # We have a document. Documents have a filename attribute.
    # Use this for choosing the exact file path.
    if media.document:
        for attribute in media.document.attributes:
            if isinstance(attribute, types.DocumentAttributeFilename):
                return (os.path.join(user_path, attribute.file_name), attribute.file_name)

    # We have a photo. Photos have no file name, thereby return the directory
    # and let telethon decide the name of the file.
    return (user_path, None)


def get_bool_from_text(text):
    """Check if we can convert this string to bool."""
    if text.lower() in ['1', 'true', 'on']:
        return True
    elif text.lower() in ['0', 'false', 'off']:
        return False
    else:
        raise Exception("Unknown boolean text")
