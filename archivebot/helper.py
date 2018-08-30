"""Some static stuff or helper functions for archive bot."""
import os
from archivebot.config import config
from telethon import types


help_text = """A handy telegram bot which allows to store files on your server, which are posted in a group chat or a normal chat.

This is great to collect images from your last holiday trip or simply to push backups or interesting files from your telegram to your server.

To send uncompressed pictures with your handy:
1. Click the share button
2. Select `File`
3. Select Gallery (To send images without compression)

Available commands:

/start Start the bot
/stop Stop the bot
/set_name Set the name for this chat. This also determines the name of the target folder on the server.
/help Show this text
"""


def get_chat_id(chat):
    """Get the id depending on the chat type."""
    if isinstance(chat, types.PeerUser):
        return chat.user_id
    elif isinstance(chat, types.PeerChat):
        return chat.chat_id
    elif isinstance(chat, types.PeerChannel):
        return chat.channel_id
    else:
        raise Exception("Unknown chat type")


def get_group_path(group_name):
    """Compile the directory path for this group."""
    return os.path.join(config.TARGET_DIR, group_name)


def get_file_path(subscriber, user, media):
    """Compile the file path and ensure the parent directories exist."""
    # Create user directory
    user_path = os.path.join(
        get_group_path(subscriber.group_name),
        user.username.lower(),
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
    return (user_path, 'undefined')
