import time
import traceback
from urllib.error import HTTPError

import bot.server.handlers.command_ui_handlers
from data_access.repository import Repository
from bot.server.handlers.handler_context import HandlerContext, \
    HandlerConfiguration
from bot.server.handlers.fallback_handlers import \
    handle_error_while_processing_update
from bot.server.models.update_context import UpdateContext
from bot.server.router import route
from services.configuration import CONFIGURATION
from services.telegram.message_manager import TelegramMessageManager
from services.logging import CompositeLogger, ConsoleLogger, DatabaseLogger, \
    FileLogger, LoggingLevel
from data_access.sqlite_connection import create_sqlite_connection

# create DB schema if it doesn't exist yet
repository = Repository(create_sqlite_connection(CONFIGURATION.DATABASE_PATH))
repository.create_schema()
repository.commit()

# set bot commands
telegram_message_manager = TelegramMessageManager(CONFIGURATION.TOKEN)
telegram_message_manager.set_bot_commands(CONFIGURATION.BOT_COMMANDS)

# create all other services
logger = CompositeLogger([
    ConsoleLogger(),
    FileLogger(CONFIGURATION.LOGS_PATH),
    DatabaseLogger(create_sqlite_connection(CONFIGURATION.DATABASE_PATH)),
])
handler_context = HandlerContext(
    telegram_message_manager,
    repository,
    logger,
    HandlerConfiguration(
        queue_name_limit=CONFIGURATION.QUEUE_NAME_LIMIT
    )
)

# the 'game' loop that listens for new messages and responds to them
logger.log(LoggingLevel.INFO, "Bot started")
while True:
    try:
        time.sleep(CONFIGURATION.PAUSE_DURATION)
        try:
            updates = telegram_message_manager.get_latest_messages()
            http_fail_counter = 0
        except HTTPError:
            logger.log(LoggingLevel.WARN, traceback.format_exc())
            time.sleep(1)
            continue
        except OSError as os_error: # this happens when the network fails
            logger.log(
                LoggingLevel.WARN,
                f"Got an OS error while fetching latest messages: {os_error}.\n"
                    + f"Stack trace:\n{traceback.format_exc()}"
            )
            time.sleep(1)

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
                target_handler(handler_context, update_context)
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
                handle_error_while_processing_update(
                    handler_context,
                    update_context
                )
            except Exception as error:
                logger.log(LoggingLevel.ERROR, traceback.format_exc())
                handle_error_while_processing_update(
                    handler_context,
                    update_context
                )
            finally:
                # finish the transaction in case there is one
                repository.commit()
    except Exception as error:
        logger.log(
            LoggingLevel.ERROR,
            f"An unhandled exception occured: {error}.\n"
                + f"Stack trace: {traceback.format_exc()}"
        )
