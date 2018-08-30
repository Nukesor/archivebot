#!/bin/env python
"""Start the bot."""
from archivebot.archivebot import archive

archive.run_until_disconnected()
