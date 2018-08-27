"""Simple wrapper around sentry that allows for lazy initilization."""
from raven import Client
from archivebot.config import config


class Sentry(object):
    """Sentry wrapper class that allows this app to work without a sentry token.

    If no token is specified in the config, the messages used for logging are simply not called.
    """

    initialized = False

    def __init__(self):
        """Construct new sentry wrapper."""
        if config.SENTRY_TOKEN is not None:
            self.initialized = True
            self.sentry = Client(config.SENTRY_TOKEN)

    def captureMessage(self, *args, **kwargs):
        """Capture message with sentry."""
        if self.initialized:
            self.sentry.captureMessage(*args, **kwargs)

    def captureException(self, *args, **kwargs):
        """Capture exception with sentry."""
        if self.initialized:
            self.sentry.captureException(*args, **kwargs)
