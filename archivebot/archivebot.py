"""A bot which downloads various files from chats."""
import os
from telethon import TelegramClient, events
import shutil

from archivebot.config import config
from archivebot.file import File # noqa
from archivebot.subscriber import Subscriber
from archivebot.sentry import sentry
from archivebot.helper import (
    get_peer_information,
    get_info_text,
    get_option_for_subscriber,
    help_text,
    possible_media,
    session_wrapper,
    should_accept_message,
    get_username,
)
from archivebot.file_helper import (
    create_file,
    create_zips,
    get_channel_path,
    init_zip_dir,
)

if config.TELEGRAM_BOT_API_KEY is None:
    NAME = 'archivebot'
else:
    NAME = config.TELEGRAM_BOT_API_KEY.split(':')[0]

archive = TelegramClient(NAME, config.TELEGRAM_APP_API_ID, config.TELEGRAM_APP_API_HASH)

# Ensure save directory for files exists
if not os.path.exists(config.TARGET_DIR):
    os.mkdir(config.TARGET_DIR)


@archive.on(events.NewMessage(pattern='/help'))
@session_wrapper()
async def help(event, session):
    """Send a help text."""
    return help_text


@archive.on(events.NewMessage(pattern='/info'))
@session_wrapper()
async def info(event, session):
    """Send a help text."""
    to_id, to_type = get_peer_information(event.message.to_id)
    subscriber = Subscriber.get_or_create(session, to_id, to_type, event.message)
    return get_info_text(subscriber)


@archive.on(events.NewMessage(pattern='/set_name'))
@session_wrapper()
async def set_name(event, session):
    """Set query attributes."""
    to_id, to_type = get_peer_information(event.message.to_id)
    new_channel_name = event.message.message.split(' ', maxsplit=1)[1].strip()
    if new_channel_name == 'zips':
        return "Invalid channel name. Pick another."

    subscriber = Subscriber.get_or_create(session, to_id, to_type, event.message,
                                          channel_name=new_channel_name)

    old_channel_path = get_channel_path(subscriber.channel_name)
    new_channel_path = get_channel_path(new_channel_name)

    new_real_path = os.path.realpath(new_channel_path)
    target_real_path = os.path.realpath(config.TARGET_DIR)
    if not new_real_path.startswith(target_real_path) or \
            new_real_path == target_real_path:
        user = await archive.get_entity(event.message.from_id)
        sentry.captureMessage("User tried to escape directory.",
                              extra={'new_channel_name': new_channel_name,
                                     'channel': subscriber.channel_name,
                                     'user': get_username(user)},
                              tags={'level': 'info'})

        return "Please stop fooling around and try to escape the directory. I have been notified as well."

    if session.query(Subscriber) \
            .filter(Subscriber.channel_name == new_channel_name) \
            .one_or_none():
        return "Channel name already exists. Please choose another one."

    elif old_channel_path != new_channel_path:
        subscriber.channel_name = new_channel_name
        if os.path.exists(old_channel_path):
            os.rename(old_channel_path, new_channel_path)
        return "Channel name changed."


@archive.on(events.NewMessage(pattern='/verbose'))
@session_wrapper()
async def set_verbose(event, session):
    """Set query attributes."""
    subscriber, value = await get_option_for_subscriber(event, session)
    if subscriber is None:
        return

    subscriber.verbose = value
    return f"I'm now configured to be {'verbose' if value else 'sneaky'}."


@archive.on(events.NewMessage(pattern='/allow_duplicates'))
@session_wrapper()
async def allow_duplicates(event, session):
    """Set query attributes."""
    subscriber, value = await get_option_for_subscriber(event, session)
    if subscriber is None:
        return

    subscriber.allow_duplicates = value
    return f"I'm now configured to {'' if value else 'not'} allow duplicate file names."


@archive.on(events.NewMessage(pattern='/sort_by_user'))
@session_wrapper()
async def set_sort_by_user(event, session):
    """Set query attributes."""
    subscriber, value = await get_option_for_subscriber(event, session)
    if subscriber is None:
        return
    subscriber.sort_by_user = value
    return f"{'Sorting' if value else 'Not sorting'} by user."


@archive.on(events.NewMessage(pattern='/accept'))
@session_wrapper()
async def accepted_media_types(event, session):
    """Set query attributes."""
    to_id, to_type = get_peer_information(event.message.to_id)
    subscriber = Subscriber.get_or_create(session, to_id, to_type, event.message)

    # Convert the incoming text into an boolean
    arguments = event.message.message.lower().split(' ')[1:]
    accepted_media = set()
    for argument in arguments:
        if argument in possible_media:
            accepted_media.add(argument)

    accepted_media = list(accepted_media)
    accepted_media.sort()

    subscriber.accepted_media = ' '.join(accepted_media)
    return f"Now accepting following media types: {accepted_media}."


@archive.on(events.NewMessage(pattern='/start'))
@session_wrapper()
async def start(event, session):
    """Start the bot."""
    to_id, to_type = get_peer_information(event.message.to_id)

    subscriber = Subscriber.get_or_create(session, to_id, to_type, event.message)
    subscriber.active = True
    session.add(subscriber)

    return 'Files posted in this channel will now be archived.'


@archive.on(events.NewMessage(pattern='/stop'))
@session_wrapper()
async def stop(event, session):
    """Stop the bot."""
    to_id, to_type = get_peer_information(event.message.to_id)

    subscriber = Subscriber.get_or_create(session, to_id, to_type, event.message)
    subscriber.active = False
    session.add(subscriber)

    return "Files won't be archived any longer."


@archive.on(events.NewMessage(pattern='/clear_history'))
@session_wrapper()
async def clear_history(event, session):
    """Stop the bot."""
    to_id, to_type = get_peer_information(event.message.to_id)
    subscriber = Subscriber.get_or_create(session, to_id, to_type, event.message)

    channel_path = get_channel_path(subscriber.channel_name)
    for known_file in subscriber.files:
        session.delete(known_file)

    if os.path.exists(channel_path):
        shutil.rmtree(channel_path)

    session.commit()

    return "All files from this chat have been deleted."


@archive.on(events.NewMessage(pattern='/scan_chat'))
@session_wrapper(addressed=False)
async def scan_chat(event, session):
    """Check if we received any files."""
    to_id, to_type = get_peer_information(event.message.to_id)
    subscriber = Subscriber.get_or_create(session, to_id, to_type, event.message)

    async for message in archive.iter_messages(event.message.to_id):
        await process_message(session, subscriber, message, event)

    return "Chat scan successful."


@archive.on(events.NewMessage(pattern='/zip'))
@session_wrapper()
async def zip(event, session):
    """Check if we received any files."""
    to_id, to_type = get_peer_information(event.message.to_id)
    subscriber = Subscriber.get_or_create(session, to_id, to_type, event.message)

    channel_path = get_channel_path(subscriber.channel_name)
    if not os.path.exists(channel_path):
        return "No files for this channel yet."

    zip_dir = init_zip_dir(subscriber.channel_name)

    text = f"Zipping started, this might take some time. Please don't issue this command again until I'm finished."
    await event.respond(text)

    create_zips(subscriber.channel_name, zip_dir, channel_path)

    text = "Zipping is completed. I'll now start uploading."
    await event.respond(text)

    for zip_file in os.listdir(zip_dir):
        zip_file_path = os.path.join(zip_dir, zip_file)
        await archive.send_file(event.message.to_id, zip_file_path)

    shutil.rmtree(zip_dir)

    return "All files are uploaded :)"


@archive.on(events.NewMessage())
@session_wrapper(addressed=False)
async def process(event, session):
    """Check if we received any files."""
    to_id, to_type = get_peer_information(event.message.to_id)
    subscriber = Subscriber.get_or_create(session, to_id, to_type, event.message)

    await process_message(session, subscriber, event.message, event)


async def process_message(session, subscriber, message, event):
    """Process a single message."""
    to_id, to_type = get_peer_information(message.to_id)

    try:
        # If this message is forwarded, get the original sender.
        if message.forward:
            user = await message.forward.get_sender()
        else:
            user = await archive.get_entity(message.from_id)
    except ValueError:
        sentry.captureMessage(
            "User tried to escape directory.",
            extra={'channel': subscriber.channel_name,
                   'from': message.from_id,
                   'forward': message.forward,
                   },
            tags={'level': 'info'})
        return

    # Check if we should accept this message
    if not await should_accept_message(event, message, user, subscriber):
        return

    # Create a new file. If it's not possible or not wanted, return None
    new_file = await create_file(session, event, subscriber, message, user)
    if new_file is None:
        return None

    # Download the file
    success = await message.download_media(str(new_file.file_path))

    # Download succeeded, if the result is not None
    if success is not None:
        # Mark the file as succeeded
        new_file.success = True
    session.commit()


def main():
    """Login and start the bot."""
    if config.TELEGRAM_BOT_API_KEY is None:
        archive.start(phone=config.TELEGRAM_PHONE_NUMBER)
    else:
        archive.start(bot_token=config.TELEGRAM_BOT_API_KEY)

    archive.run_until_disconnected()
