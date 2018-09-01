"""Some static stuff or helper functions for archive bot."""
import asyncio
import traceback
from telethon import types

from archivebot.db import get_session
from archivebot.sentry import sentry


possible_media = ['document', 'photo']

help_text = f"""A handy telegram bot which allows to store files on your server, which are posted in a chat.
For example, this is great to collect images and videos from all members of your last holiday trip or simply to push backups or interesting files from your telegram chats to your server.

If you forward messages from other chats and `sort_by_user` is on, the file will still be saved under the name of the original owner.

To send multiple uncompressed pictures and videos with your phone:
1. Click the share button
2. Select `File`
3. Select Gallery (To send images without compression)

In group channels the bot expects a command in combination with its username.
E.g. /start@bot_user_name

Feel free to contribute or look at the code at https://github.com/Nukesor/archivebot

Available commands:

/start Start the bot
/stop Stop the bot
/set_name Set the name for this chat. This also determines the name of the target folder on the server.
/verbose ['true', 'false'] The bot will complain if there are duplicate files or uncompressed images are sent, whilst not being accepted.
/sort_by_user [true, false] Incoming files will be sorted by user in the server directory for this chat.
/accept {possible_media} Specify the allowed media types. Always provide a space separated list of all accepted media types, e.g. 'document photo'.
/info Show current settings.
/help Show this text
"""


def get_info_text(subscriber):
    """Format the info text."""
    return f"""Current settings:

Name: {subscriber.channel_name}
Active: {subscriber.active}
Accepted Media: {subscriber.accepted_media}
Verbose: {subscriber.verbose}
Sort files by User: {subscriber.sort_by_user}
"""


def session_wrapper(addressed=True):
    """Allow to differentiate between addressed commands and all messages."""
    def real_session_wrapper(func):
        """Wrap a telethon event to create a session and handle exceptions."""
        async def wrapper(event):
            if addressed:
                # Check if this message is meant for us
                bot_user = await event.client.get_me()
                username = bot_user.username
                recipient_string = f'@{username}'
                _, chat_type = get_chat_information(event.message.to_id)

                # Accept all commands coming directly from a user
                # Only accept commands send with an recipient string
                if chat_type != 'user':
                    command = event.message.message.split(' ', maxsplit=1)[0]
                    if recipient_string not in command:
                        return

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

    return real_session_wrapper


def get_username(user):
    """Get a username from a user."""
    if user.username:
        return user.username
    elif user.first_name:
        return user.first_name
    elif user.last_name:
        return user.last_name


def get_chat_information(chat):
    """Get the id depending on the chat type."""
    if isinstance(chat, types.PeerUser):
        return chat.user_id, 'user'
    elif isinstance(chat, types.PeerChat):
        return chat.chat_id, 'chat'
    elif isinstance(chat, types.PeerChannel):
        return chat.channel_id, 'channel'
    else:
        raise Exception("Unknown chat type")


def get_bool_from_text(text):
    """Check if we can convert this string to bool."""
    if text.lower() in ['1', 'true', 'on']:
        return True
    elif text.lower() in ['0', 'false', 'off']:
        return False
    else:
        raise Exception("Unknown boolean text")


def should_accept_message(subscriber, message, user):
    """Check if we should accept this message."""
    if subscriber.active is False:
        return False

    # No media => not interesting
    if message.media is None:
        return False

    # We only want messages from users
    if not isinstance(user, types.User):
        return False

    return True
