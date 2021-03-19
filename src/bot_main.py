import json
from os import path
import sqlite3
import time
import traceback
from urllib.error import HTTPError

from data_access.repository import Repository
from bot.server.controller import Controller, ControllerConfiguration
from bot.server.models.update_context import UpdateContext
from bot.server.router import route
from services.telegram.message_manager import TelegramMessageManager
from services.logging import CompositeLogger, ConsoleLogger, FileLogger, \
    LoggingLevel

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
LOGS_PATH = path.join(PROJECT_PATH, configuration["logs"])
PAUSE_DURATION = configuration["pause"]
QUEUE_NAME_LIMIT = configuration["queue_name_limit"]
BOT_USERNAME = configuration["bot_username"]

# create DB schema if it doesn't exist yet
with sqlite3.connect(DATABASE_PATH) as connection:
    repository = Repository(connection)
    repository.create_schema()
    repository.commit()

telegram_message_manager = TelegramMessageManager(TOKEN)

bot_commands_file_path = path.join(PROJECT_PATH, "config", "bot_commands.json")
with open(bot_commands_file_path, encoding="UTF-8") as bot_commands_file:
    telegram_message_manager.set_bot_commands(bot_commands_file.read())

logger = CompositeLogger([
    ConsoleLogger(),
    FileLogger(LOGS_PATH),
])

# the 'game' loop that listens for new messages and responds to them
try:
    logger.log(LoggingLevel.INFO, "Bot started")
    while True:
        time.sleep(PAUSE_DURATION)

        updates = telegram_message_manager.get_latest_messages()

        with sqlite3.connect(DATABASE_PATH) as connection:
            repository = Repository(connection)
            controller = Controller(
                telegram_message_manager,
                repository,
                logger,
                ControllerConfiguration(queue_name_limit=QUEUE_NAME_LIMIT)
            )

            # iterate over the latest messages for update in updates:
            for update in updates:
                update_context = UpdateContext.from_update(update)
                target_handler = route(update_context, BOT_USERNAME)
                if target_handler is None:
                    logger.log(
                        LoggingLevel.ERROR,
                        f"Could not route update: {update}"
                    )
                    continue
                try:
                    target_handler(controller, update_context)
                except KeyboardInterrupt:
                    exit()
                except HTTPError as http_error:
                    logger.log(
                        LoggingLevel.ERROR,
                        "Encountered an HTTP error\n"
                        + "Stack trace:\n"
                        + f"{traceback.format_exc()}\n"
                        + f"URL: {http_error.url}\n"
                        + "Response: "
                        + f"{http_error.file.read().decode('UTF-8')}\n\n"
                    )
                    controller.handle_error_while_processing_update(
                        update_context
                    )
                except Exception as error:
                    logger.log(LoggingLevel.ERROR, traceback.format_exc())
                    controller.handle_error_while_processing_update(
                        update_context
                    )
except Exception as error:
    logger.log(
        LoggingLevel.ERROR,
        f"An unhandled exception occured: {error}"
    )
    raise error
finally:
    logger.log(LoggingLevel.INFO, "Bot stopped")
