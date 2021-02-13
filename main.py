import time
from os import path
import sqlite3
import traceback
from urllib.error import HTTPError

from repository import Repository
from telegram_message_manager import TelegramMessageManager
from controller import Controller
from router import route
from models.update_context import UpdateContext

# constants
TOKEN_FILE_NAME = "token"
DATABASE_NAME = "nureq.db"

# load the token if available
if not path.exists(TOKEN_FILE_NAME):
    print("You need the token file")
    exit(1)

with open(TOKEN_FILE_NAME) as token_file:
    token = token_file.readline()
    if token[-1] == "\n":
        token = token[:-1]

# create DB schema if it doesn't exist yet
with sqlite3.connect(DATABASE_NAME) as connection:
    repository = Repository(connection)
    repository.create_schema()
    repository.commit()

telegram_message_manager = TelegramMessageManager(token)

with open("bot_commands.json", encoding="UTF-8") as bot_commands_file:
    telegram_message_manager.set_bot_commands(bot_commands_file.read())

# the 'game' loop that listens for new messages and responds to them
while True:
    time.sleep(0.1)

    updates = telegram_message_manager.get_latest_messages()

    with sqlite3.connect(DATABASE_NAME) as connection:
        repository = Repository(connection)
        controller = Controller(telegram_message_manager, repository)

        # iterate over the latest messages for update in updates:
        for update in updates:
            update_context = UpdateContext.from_update(update)
            target_handler = route(update_context)
            if target_handler is None:
                print(f"Could not route update: {update}")
                continue
            try:
                target_handler(controller, update_context)
            except KeyboardInterrupt:
                exit()
            except HTTPError as http_error:
                print(
                    "Encountered an HTTP error\n"
                    + "Stack trace:\n"
                    + f"{traceback.format_exc()}\n"
                    + f"URL: {http_error.url}\n"
                    + f"Response: {http_error.file.read().decode('UTF-8')}\n\n"
                )
                controller.handle_error_while_processing_update(update_context)
            except Exception as error:
                print(traceback.format_exc())
                controller.handle_error_while_processing_update(update_context)
