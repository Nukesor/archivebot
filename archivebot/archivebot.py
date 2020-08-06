"""A bot which downloads various files from chats."""
import os
import time
from telethon import TelegramClient, events, types
from telethon.errors import BadMessageError, FloodWaitError
import shutil

from archivebot.config import config
from archivebot.sentry import sentry
from archivebot.models import (  # noqa
    File,
    Subscriber,
)

from archivebot.helper import (
    get_peer_information,
    get_info_text,
    get_option_for_subscriber,
    help_text,
    possible_media,
    should_accept_message,
    get_username,
    UnknownUser,
)
from archivebot.helper.session import session_wrapper
from archivebot.helper.file import (
    create_file,
    create_zips,
    get_chat_path,
    init_zip_dir,
)

if config["telegram"]["userbot"]:
    NAME = "archivebot"
else:
    NAME = config["telegram"]["api_key"].split(":")[0]

archive = TelegramClient(
    NAME, config["telegram"]["app_api_id"], config["telegram"]["app_api_hash"]
)

# Ensure save directory for files exists
if not os.path.exists(config["download"]["target_dir"]):
    os.mkdir(config["download"]["target_dir"])


@archive.on(events.NewMessage(pattern="/help", outgoing=True))
@session_wrapper()
async def help(event, session):
    """Send a help text."""
    return help_text


@archive.on(events.NewMessage(pattern="/info", outgoing=True))
@session_wrapper()
async def info(event, session):
    """Send a the information about the current user settings."""
    to_id, to_type = get_peer_information(event.message.to_id)
    subscriber = Subscriber.get_or_create(session, to_id, to_type, event.message)
    return get_info_text(subscriber)


@archive.on(events.NewMessage(pattern="/set_name", outgoing=True))
@session_wrapper()
async def set_name(event, session):
    """Set the name of the current chat (also affects the saving directory."""
    to_id, to_type = get_peer_information(event.message.to_id)
    new_chat_name = event.message.message.split(" ", maxsplit=1)[1].strip()
    # We already save to zips, prevent that
    if new_chat_name == "zips":
        return "Invalid chat name. Pick another."

    subscriber = Subscriber.get_or_create(
        session, to_id, to_type, event.message, chat_name=new_chat_name
    )

    old_chat_path = get_chat_path(subscriber.chat_name)
    new_chat_path = get_chat_path(new_chat_name)

    # Handle any command that tries to escape the download directory
    new_real_path = os.path.realpath(new_chat_path)
    target_real_path = os.path.realpath(config["download"]["target_dir"])
    if (
        not new_real_path.startswith(target_real_path)
        or new_real_path == target_real_path
    ):
        user = await archive.get_entity(types.PeerUser(event.message.from_id))
        sentry.captureMessage(
            "User tried to escape directory.",
            extra={
                "new_chat_name": new_chat_name,
                "chat": subscriber.chat_name,
                "user": get_username(user),
            },
            tags={"level": "info"},
        )

        return "Please stop fooling around and don't try to escape the directory. I have been notified about this."

    # Check whether we already have a chat with this name
    if (
        session.query(Subscriber)
        .filter(Subscriber.chat_name == new_chat_name)
        .one_or_none()
    ):
        return "Chat name already exists. Please choose another one."

    # Move the old directory to the new location
    elif old_chat_path != new_chat_path:
        subscriber.chat_name = new_chat_name
        if os.path.exists(old_chat_path):
            os.rename(old_chat_path, new_chat_path)
        return "Chat name changed."


@archive.on(events.NewMessage(pattern="/verbose", outgoing=True))
@session_wrapper()
async def set_verbose(event, session):
    """Set the verbosity for this chat."""
    subscriber, verbose = await get_option_for_subscriber(event, session)
    if subscriber is None:
        return

    subscriber.verbose = verbose
    return f"I'm now configured to be {'verbose' if verbose else 'sneaky'}."


@archive.on(events.NewMessage(pattern="/allow_duplicates", outgoing=True))
@session_wrapper()
async def allow_duplicates(event, session):
    """Set whether duplicat file names are allowed for this chat."""
    subscriber, allowed = await get_option_for_subscriber(event, session)
    if subscriber is None:
        return

    subscriber.allow_duplicates = allowed
    return (
        f"I'm now configured to {'' if allowed else 'not'} allow duplicate file names."
    )


@archive.on(events.NewMessage(pattern="/sort_by_user", outgoing=True))
@session_wrapper()
async def set_sort_by_user(event, session):
    """Set whether files should be sorted by message author."""
    subscriber, sorting = await get_option_for_subscriber(event, session)
    if subscriber is None:
        return
    subscriber.sort_by_user = sorting
    return f"{'Sorting' if sorting else 'Not sorting'} by user."


@archive.on(events.NewMessage(pattern="/accept", outgoing=True))
@session_wrapper()
async def accepted_media_types(event, session):
    """Set the allowed media types for this chat."""
    to_id, to_type = get_peer_information(event.message.to_id)
    subscriber = Subscriber.get_or_create(session, to_id, to_type, event.message)

    # Convert the incoming text into an boolean
    arguments = event.message.message.lower().split(" ")[1:]
    accepted_media = set()
    for argument in arguments:
        if argument in possible_media:
            accepted_media.add(argument)

    accepted_media = list(accepted_media)
    accepted_media.sort()

    subscriber.accepted_media = " ".join(accepted_media)
    return f"Now accepting following media types: {accepted_media}."


@archive.on(events.NewMessage(pattern="/start", outgoing=True))
@session_wrapper()
async def start(event, session):
    """Subscribe to this specific chat."""
    to_id, to_type = get_peer_information(event.message.to_id)

    subscriber = Subscriber.get_or_create(session, to_id, to_type, event.message)
    subscriber.active = True
    session.add(subscriber)

    return "Files posted in this chat will now be archived."


@archive.on(events.NewMessage(pattern="/stop", outgoing=True))
@session_wrapper()
async def stop(event, session):
    """Unsubscribe from this specific chat."""
    to_id, to_type = get_peer_information(event.message.to_id)

    subscriber = Subscriber.get_or_create(session, to_id, to_type, event.message)
    subscriber.active = False
    session.add(subscriber)

    return "Files won't be archived any longer."


@archive.on(events.NewMessage(pattern="/clear_history", outgoing=True))
@session_wrapper()
async def clear_history(event, session):
    """Remove every downloaded file from the database and the file system."""
    to_id, to_type = get_peer_information(event.message.to_id)
    subscriber = Subscriber.get_or_create(session, to_id, to_type, event.message)

    chat_path = get_chat_path(subscriber.chat_name)
    for known_file in subscriber.files:
        session.delete(known_file)

    if os.path.exists(chat_path):
        shutil.rmtree(chat_path)

    session.commit()

    return "All files from this chat have been deleted."


@archive.on(events.NewMessage(pattern="/scan_chat", outgoing=True))
@session_wrapper()
async def scan_chat(event, session):
    """Scan the whole chat for files. Necessary for getting old files."""
    to_id, to_type = get_peer_information(event.message.to_id)
    subscriber = Subscriber.get_or_create(session, to_id, to_type, event.message)

    await event.respond("Starting full chat scan.")
    async for message in archive.iter_messages(event.message.to_id):
        try:
            await process_message(session, subscriber, message, event, full_scan=True)
        except BadMessageError:
            # Ignore bad message errors
            return

    return "Full chat scan successful."


@archive.on(events.NewMessage(pattern="/zip", outgoing=True))
@session_wrapper()
async def zip(event, session):
    """Create 1.5GB zips with all files collectd in this chat."""
    to_id, to_type = get_peer_information(event.message.to_id)
    subscriber = Subscriber.get_or_create(session, to_id, to_type, event.message)

    chat_path = get_chat_path(subscriber.chat_name)
    if not os.path.exists(chat_path):
        return "No files for this chat yet."

    zip_dir = init_zip_dir(subscriber.chat_name)

    text = f"Zipping started, this might take some time. Please don't issue this command again until I'm finished."
    await event.respond(text)

    create_zips(subscriber.chat_name, zip_dir, chat_path)

    zip_files = sorted(os.listdir(zip_dir))
    zip_files_count = len(zip_files)

    text = f"Zipping is completed. I'll now start uploading {zip_files_count} file(s)."
    await event.respond(text)

    for zip_file in zip_files:
        zip_file_path = os.path.join(zip_dir, zip_file)
        await archive.send_file(event.message.to_id, zip_file_path)

    shutil.rmtree(zip_dir)

    return "All files are uploaded :)"


@archive.on(events.NewMessage())
@session_wrapper(addressed=False)
async def process(event, session):
    """Main entry for processing messages and downloading files."""
    to_id, to_type = get_peer_information(event.message.to_id)
    subscriber = Subscriber.get_or_create(session, to_id, to_type, event.message)

    try:
        await process_message(session, subscriber, event.message, event)
    except BadMessageError:
        # Ignore bad message errors
        return


async def process_message(session, subscriber, message, event, full_scan=False):
    """Process a single message. Check if it has a file we want to download."""
    to_id, to_type = get_peer_information(message.to_id)

    try:
        # If this message is forwarded, get the original sender.
        if message.forward and message.forward.sender_id is not None:
            user_id = message.forward.sender_id
            user = await archive.get_entity(user_id)

            # A channel can be a sender as well, early return if the sender is no User
            if not isinstance(user, types.User):
                return

        else:
            # Ignore messages with no sent user
            if message.from_id is None:
                return

            user_id = message.from_id
            user = await archive.get_entity(message.from_id)

        # Check if we should accept this message
        if not await should_accept_message(event, message, user, subscriber):
            return

        # Create a new file. If it's not possible or not wanted, return None
        new_file = await create_file(
            session, event, subscriber, message, user, full_scan
        )
        if new_file is None:
            return None

        # Download the file
        success = await message.download_media(str(new_file.file_path))

        # Download succeeded, if the result is not None
        if success is not None:
            # Mark the file as succeeded
            new_file.success = True
        session.commit()

    except ValueError:
        # Handle broadcast channels those have None for user_id:
        if user_id is None:
            user_id = subscriber.chat_name
        user = UnknownUser(user_id)

    # We got a flood wait error. Wait for the specified time and recursively retry
    except FloodWaitError as e:
        time.sleep(e.seconds + 1)
        process_message(session, subscriber, message, event, full_scan)
        return


def main():
    """Login and start the bot."""
    if config["telegram"]["userbot"]:
        archive.start(phone=config["telegram"]["phone_number"])
    else:
        archive.start(bot_token=config["telegram"]["api_key"])

    archive.run_until_disconnected()
