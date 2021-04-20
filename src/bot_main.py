import time
import traceback
from urllib.error import HTTPError

from data_access.repository import Repository
from bot.server.controller import Controller, ControllerConfiguration
from bot.server.models.update_context import UpdateContext
from bot.server.router import route
from services.configuration import CONFIGURATION
from services.telegram.message_manager import TelegramMessageManager
from services.logging import CompositeLogger, ConsoleLogger, FileLogger, \
    LoggingLevel
from data_access.sqlite_connection import create_sqlite_connection

# create DB schema if it doesn't exist yet
with create_sqlite_connection(CONFIGURATION.DATABASE_PATH) as connection:
    repository = Repository(connection)
    repository.create_schema()
    repository.commit()

telegram_message_manager = TelegramMessageManager(CONFIGURATION.TOKEN)

telegram_message_manager.set_bot_commands(CONFIGURATION.BOT_COMMANDS)

logger = CompositeLogger([
    ConsoleLogger(),
    FileLogger(CONFIGURATION.LOGS_PATH),
])

# the 'game' loop that listens for new messages and responds to them
try:
    logger.log(LoggingLevel.INFO, "Bot started")
    while True:
        time.sleep(CONFIGURATION.PAUSE_DURATION)

        updates = telegram_message_manager.get_latest_messages()

        with create_sqlite_connection(CONFIGURATION.DATABASE_PATH) \
                as connection:
            repository = Repository(connection)
            controller = Controller(
                telegram_message_manager,
                repository,
                logger,
                ControllerConfiguration(
                    queue_name_limit=CONFIGURATION.QUEUE_NAME_LIMIT
                )
            )

            # iterate over the latest messages for update in updates:
            for update in updates:
                update_context = UpdateContext.from_update(update)
                target_handler = route(
                    update_context,
                    CONFIGURATION.BOT_USERNAME
                )
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
