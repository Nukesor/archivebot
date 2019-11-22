"""Helper module for file helper."""
import os
import subprocess
from telethon import types
from datetime import datetime

from archivebot.models.file import File
from archivebot.config import config
from archivebot.sentry import sentry
from archivebot.helper import (
    get_username,
    get_peer_information,
)


async def create_file(session, event, subscriber, message, user, full_scan):
    """Create a file object from a message."""
    to_id, to_type = get_peer_information(message.to_id)

    file_type, file_id = await get_file_information(event, message, subscriber, user, full_scan)
    if not file_type:
        return None

    # Check if this exact file from the same message is already downloaded.
    # This is a hard constraint which shouldn't be violated.
    if File.exists(session, subscriber, file_id):
        return None

    # The file path is depending on the media type.
    # In case such a file already exists and duplicate files are disabled, the function returns None.
    # In that case we will return early.
    file_path, file_name = get_file_path(subscriber, get_username(user), message)

    # Don't check zipped files from ourselves.
    # Otherwise we would double in size on each /scan_chat /zip command combination
    me = await event.client.get_me()
    splitted = file_name.rsplit('.', maxsplit=2)
    if user.id == me.id and len(splitted) == 3 and splitted[1] == '7z':
        return None

    if file_path is None:
        # Inform the user about duplicate files
        if subscriber.verbose:
            text = f"File with name {file_name} already exists."
            await event.respond(text)

        sentry.captureMessage("File already exists",
                              extra={'file_path': file_path,
                                     'file_name': file_name,
                                     'chat': subscriber.chat_name,
                                     'user': get_username(user)},
                              tags={'level': 'info'})
        return None

    # The file path is depending on the media type.
    new_file = File(file_id, to_id, user.id,
                    subscriber, to_type, message.id,
                    file_type, file_name, file_path)

    session.add(new_file)
    session.commit()

    return new_file


def get_chat_path(chat_name):
    """Compile the directory path for this chat."""
    return os.path.join(config['download']['target_dir'], chat_name)


def init_zip_dir(chat_name):
    """Create the zip directory for this chat."""
    zip_dir = os.path.join(config['download']['target_dir'], 'zips')
    if not os.path.exists(zip_dir):
        os.mkdir(zip_dir)

    zip_dir = os.path.join(zip_dir, chat_name)
    if not os.path.exists(zip_dir):
        os.mkdir(zip_dir)

    return zip_dir


def get_zip_file_path(chat_name):
    """Compile the directory path for the zip directory of this chat."""
    return os.path.join(config['download']['target_dir'], 'zips', chat_name)


def get_file_path(subscriber, username, message):
    """Compile the file path and ensure the parent directories exist."""
    # If we don't sort by user, use the chat_path
    if not subscriber.sort_by_user:
        directory = get_chat_path(subscriber.chat_name)
    # sort_by_user is active. Add the user directory.
    else:
        directory = os.path.join(
            get_chat_path(subscriber.chat_name),
            username.lower(),
        )

    # Create the directory
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

    # We have a document. Documents have a filename attribute.
    # Use this for choosing the exact file path.
    if message.document:
        for attribute in message.document.attributes:
            # Document has a file name attribute
            if isinstance(attribute, types.DocumentAttributeFilename):
                file_name = attribute.file_name
                # Path exists. Return None if duplicate files are disallowed.
                if os.path.exists(os.path.join(directory, file_name)):
                    if not subscriber.allow_duplicates:
                        return None, file_name
                    else:
                        file_name = find_file_name(directory, file_name)

                file_path = os.path.join(directory, file_name)
                return (file_path, file_name)

    file_name = datetime.now().strftime('media_%Y-%m-%d_%H-%M-%S')
    file_path = os.path.join(directory, file_name)
    # We have a photo. Photos have no file name, thereby return the directory
    # and let telethon decide the name of the file.
    return (file_path, file_name)


def find_file_name(directory, file_name):
    """Find a file name which doesn't exist yet."""
    counter = 1
    original_file_name, extension = os.path.splitext(file_name)
    file_name = f"{original_file_name}_{counter}{extension}"
    while os.path.exists(os.path.join(directory, file_name)):
        counter += 1
        file_name = f"{original_file_name}_{counter}{extension}"

    return file_name


async def get_file_information(event, message, subscriber, user, full_scan):
    """Extract and return all information about the given file.

        At the same time we check, whether we actually want this file.
        In case we don't, return None, None
    """
    file_id = None
    file_type = None

    accepted_media = subscriber.accepted_media.split(' ')

    # Check for stickers
    if 'sticker' in accepted_media and message.sticker is not None:
        file_type = 'sticker'
        file_id = message.document.id

    # We just got a sticker, but we don't want any
    elif message.sticker is not None:
        return None, None

    # Check for a document
    if 'document' in accepted_media and message.document is not None:
        file_type = 'document'
        file_id = message.document.id

    # Check for a photo
    if 'photo' in accepted_media and message.photo is not None:
        file_type = 'photo'
        file_id = message.photo.id
    elif message.photo is not None:
        # Flame the user that compressed photos are evil
        if subscriber.verbose and full_scan:
            text = f"Please send uncompressed files @{user.username} :(."
            await event.respond(text)

    return file_type, file_id


def create_zips(chat_name, zip_dir, target_dir):
    """Create a zip file from a given dir path."""
    file_name = os.path.join(zip_dir, chat_name)
    command = ["7z", "-v1400m", "a", f"{file_name}.7z", target_dir]

    subprocess.run(command)
