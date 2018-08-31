"""Helper module for file helper."""
import os
import asyncio
from telethon import types

from archivebot.config import config
from archivebot.sentry import sentry
from archivebot.helper import get_username


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


async def check_if_file_exists(event, file_path, file_name, subscriber, user):
    """Check whether the filename already exists."""
    if not os.path.isdir(file_path) and os.path.exists(file_path):
        # Inform the user about duplicate files
        if subscriber.verbose:
            text = f"File with name {file_name} already exists."
            await asyncio.wait([event.respond(text)])

        sentry.captureMessage(
            "File already exists",
            extra={
                'file_path': file_path,
                'file_name': file_name,
                'channel': subscriber.channel_name,
                'user': get_username(user),
            },
            tags={'level': 'info'},
        )
        return True

    False
