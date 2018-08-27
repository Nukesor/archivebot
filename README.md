# Archive-Bot

A handy telegram bot which allows to store files on your server, which are posted in a group chat or a normal chat.

This is great to collect images from your last holiday trip or simply to push backups or interesting files from your telegram to your server.

To send uncompressed pictures with your handy:
1. Click the share button
2. Select `File`
3. Select Gallery (To send images without compression)

Available commands:

    /start Start the bot
    /stop Stop the bot
    /set_name Set the name for this chat. This also determines the name of the target folder on the server.

Feel free to host your own or to use mine: @NukesArchiveBot

## Installation and starting:

Clone the repository: 

    % git clone git@github.com:nukesor/archivebot && cd archivebot

Now copy the `archivebot/config.example.py` to `archivebot/config.py` and adjust all necessary values.
Finally execute following commands to install all dependencies and to start the bot:

    % make
    % ./venv/bin/activate
    % ./initdb.py
    % ./main.py

## Todos and Ideas:

- Allow to filter for different mime types per group.
