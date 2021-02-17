import json
from os import path
import sqlite3
import time
import traceback
from urllib.error import HTTPError

from data_access.repository import Repository
from server.controller import Controller
from server.models.update_context import UpdateContext
from server.router import route
from services.telegram_message_manager import TelegramMessageManager

# configuration
PROJECT_PATH = path.abspath(path.join(__file__, "..", ".."))

config_file_path = path.join(PROJECT_PATH, "config", "configuration.json")
with open(config_file_path) as configuration_file:
    configuration = json.loads(configuration_file.read())

TOKEN_PATH = path.join(PROJECT_PATH, configuration["token"])
# load the token if available
if not path.exists(TOKEN_PATH):
    print(f"You need the token file at {TOKEN_PATH}")
    exit(1)

with open(TOKEN_PATH) as token_file:
    TOKEN = token_file.readline()
    if TOKEN[-1] == "\n":
        TOKEN = TOKEN[:-1]

DATABASE_PATH = path.join(PROJECT_PATH, configuration["database"])

# create DB schema if it doesn't exist yet
with sqlite3.connect(DATABASE_PATH) as connection:
    repository = Repository(connection)
    repository.create_schema()
    repository.commit()

telegram_message_manager = TelegramMessageManager(TOKEN)

bot_commands_file_path = path.join(PROJECT_PATH, "config", "bot_commands.json")
with open(bot_commands_file_path, encoding="UTF-8") as bot_commands_file:
    telegram_message_manager.set_bot_commands(bot_commands_file.read())

# the 'game' loop that listens for new messages and responds to them
while True:
    time.sleep(0.1)

    updates = telegram_message_manager.get_latest_messages()

    with sqlite3.connect(DATABASE_PATH) as connection:
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
