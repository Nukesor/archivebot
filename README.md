# Archive-Bot

A handy telegram bot which allows to store files on your server, which are posted in a group chat or a normal chat.

This is great to collect images and videos from your last holiday trip or simply to push backups or interesting files from your telegram to your server.

If you forward messages from other chats, the file will still be saved under the name of the original owner

To send multiple uncompressed pictures and videos with your phone:
1. Click the share button
2. Select `File`
3. Select Gallery (To send images without compression)

## Features:

- Custom name for chats for easier server file management.
- By default sorts incoming files by user and chat, but this can be disabled.
- Verbose option to notify users of duplicates or compressed images.
- Filtering of accepted media types.
- Proper handling of forwarded messages


## Installation and starting:

Clone the repository: 

    % git clone git@github.com:nukesor/archivebot && cd archivebot

Now copy the `archivebot/config.example.py` to `archivebot/config.py` and adjust all necessary values.
Finally execute following commands to install all dependencies, initialize the database and to start the bot:

    % make
    % ./venv/bin/activate
    % ./initdb.py
    % ./main.py


## Available commands:

    /start Start the bot
    /stop Stop the bot
    /set_name Set the name for this chat. This also determines the name of the target folder on the server.
    /verbose [true, false]
    /accept  Specify the allowed media types. Always provide a space separated list of all accepted media types, e.g. 'document photo'.
    /sort_by_user [true, false]
    /help Show this text
