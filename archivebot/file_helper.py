"""Helper module for file helper."""
import os
import subprocess
from telethon import types
from datetime import datetime

from archivebot.config import config
from archivebot.sentry import sentry
from archivebot.helper import get_username
from archivebot.file import File


async def create_file(session, event, subscriber,
                      message, user, chat_id, chat_type):
    """Create a file object."""
    file_type, file_id = await get_file_information(event, message, subscriber, user)
    if not file_type:
        return

    # Check if this exact file from the same message is already downloaded.
    # This is a hard constraint which shouldn't be violated.
    if File.exists(session, chat_id, file_id):
        return

    # The file path is depending on the media type.
    # In case such a file already exists and duplicate files are disabled, the function returns None.
    # In that case we will return early.
    file_path, file_name = get_file_path(subscriber, get_username(user), message)
    if file_path is None:
        # Inform the user about duplicate files
        if subscriber.verbose:
            text = f"File with name {file_name} already exists."
            await event.respond(text)

        sentry.captureMessage("File already exists",
                              extra={'file_path': file_path,
                                     'file_name': file_name,
                                     'channel': subscriber.channel_name,
                                     'user': get_username(user)},
                              tags={'level': 'info'})
        return None

    # The file path is depending on the media type.
    new_file = File(file_id, chat_id, chat_type,
                    user.id, message.id,
                    file_type, file_name, file_path)

    session.add(new_file)
    session.commit()

    return new_file


def get_channel_path(channel_name):
    """Compile the directory path for this channel."""
    return os.path.join(config.TARGET_DIR, channel_name)


def init_zip_dir(channel_name):
    """Compile the directory path for this channel."""
    zip_dir = os.path.join(config.TARGET_DIR, 'zips')
    if not os.path.exists(zip_dir):
        os.mkdir(zip_dir)

    zip_dir = os.path.join(zip_dir, channel_name)
    if not os.path.exists(zip_dir):
        os.mkdir(zip_dir)

    return zip_dir


def get_zip_file_path(channel_name):
    """Compile the directory path for this channel."""
    return os.path.join(config.TARGET_DIR, 'zips', channel_name)


def get_file_path(subscriber, username, message):
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
    original_filename, extension = os.path.splitext()
    file_name = f"{file_name}_{counter}{extension}"
    while os.path.exists(os.path.join(directory, file_name)):
        counter += 1
        file_name = f"{file_name}_{counter}{extension}"

    return file_name


async def get_file_information(event, message, subscriber, user):
    """Check whether we got an allowed file type."""
    file_id = None
    file_type = None

    accepted_media = subscriber.accepted_media.split(' ')

    if 'photo' in accepted_media \
            and message.photo is not None:
        file_type = 'photo'
        file_id = message.photo.id
    elif message.photo is not None:
        # Flame the user that compressed photos are evil
        if subscriber.verbose:
            text = f"Please send uncompressed files @{user.username} :(."
            await event.respond(text)

    if 'document' in accepted_media \
            and message.document is not None:
        file_type = 'document'
        file_id = message.document.id

    return file_type, file_id


def create_zips(channel_name, zip_dir, target_dir):
    """Create a zip file from given dir path."""
    file_name = os.path.join(zip_dir, channel_name)
    command = ["7z", "-v1200m", "a", f"{file_name}.7z", target_dir]

    subprocess.run(command)
