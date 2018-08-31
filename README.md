# Archive-Bot

A handy bot which enables to download files from telegram chats to your server.

For instance, this is great to collect images and videos from the members of your last holiday trip or to simply push backups or interesting files from your telegram chats to your server.

To send multiple uncompressed pictures and videos with your phone:
1. Click the share button
2. Select `File`
3. Select Gallery (To send images without compression)

## Features:

- Custom name for chats for easier server file management.
- By default, archive bot sorts incoming files by chat and then by user. The sort by user can be disabled.
- Verbose option for notifying users of duplicates or compressed images.
- Only accept specified media types.
- Properly handle forwarded messages (If sort_by_user is enabled, the original sender will be used).


## Installation and starting:

Clone the repository: 

    % git clone git@github.com:nukesor/archivebot && cd archivebot

Now copy the `archivebot/config.example.py` to `archivebot/config.py` and adjust all necessary values.
Finally execute following commands to install all dependencies, initialize the database and to start the bot:

    % make
    % ./venv/bin/activate
    % ./initdb.py
    % ./main.py


## Commands:
In group channels the bot expects a command in combination with its username.
E.g. /start@bot_user_name

    /start Start the bot
    /stop Stop the bot
    /set_name Set the name for this chat. This also determines the name of the target folder on the server.
    /verbose ['true', 'false'] The bot will complain if there are duplicate files or uncompressed images are sent, whilst not being accepted.
    /sort_by_user ['true', 'false'] Incoming files will be sorted by user in the server directory for this chat.
    /accept ['document', 'photo'] Specify the accepted media Example: '/accept document photo'
    /info Show current settings.
    /help Show this text



### Botfather commands:
These are the command descriptions formatted for the botfather, in case you want to host your own bot

    start - Start archiving Files for this chat
    stop - Stop archiving Files for this chat
    set_name - Set the name for this chat. This also determines the name of the target folder on the server.
    sort_by_user - ['true', 'false'] Incoming files will be sorted by user in the server directory for this chat.
    accept - ['document', 'photo'] Specify the allowed media types. Example: `/accept document photo`
    verbose - ['true', 'false'] The bot will complain if there are duplicate files or uncompressed images are sent, whilst not being accepted.
    info - Show current settings.
    help - Show the help text.
