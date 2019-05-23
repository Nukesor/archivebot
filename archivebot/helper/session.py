"""Session handling for commands."""
import traceback
from archivebot.db import get_session
from archivebot.sentry import sentry


def session_wrapper(addressed=True):
    """Allow to differentiate between addressed commands and all messages."""
    def real_session_wrapper(func):
        """Wrap a telethon event to create a session and handle exceptions."""
        async def wrapper(event):
            if addressed:
                # Check if this message is meant for us
                bot_user = await event.client.get_me()
                username = bot_user.username.lower()
                recipient_string = f'@{username}'

                # Accept all commands coming directly from a user
                # Only accept commands send with an recipient string
                command = event.message.message.split(' ', maxsplit=1)[0]
                if recipient_string not in command.lower():
                    return

            session = get_session()
            try:
                response = await func(event, session)
                session.commit()
                if response:
                    await event.respond(response)
            except BaseException:
                if addressed:
                    await event.respond("Some unknown error occurred.")
                traceback.print_exc()
                sentry.captureException()
            finally:
                session.remove()
        return wrapper

    return real_session_wrapper
