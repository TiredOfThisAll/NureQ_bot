import time
from os import path
import sqlite3
import traceback
import json
from urllib.error import HTTPError

from repository import Repository
from telegram_message_manager import TelegramMessageManager
from controller import Controller, ButtonCallbackType

# constants
TOKEN_FILE_NAME = "token"
DATABASE_NAME = "nureq.db"

NEW_QUEUE_COMMAND_RESPONSE_TEXT \
    = "Введите имя новой очереди в ответ на это сообщение"

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

with open("bot_commands.json") as bot_commands_file:
    telegram_message_manager.set_bot_commands(bot_commands_file.read())

# the 'game' loop that listens for new messages and responds to them
while True:
    time.sleep(1)

    updates = telegram_message_manager.get_latest_messages()

    with sqlite3.connect(DATABASE_NAME) as connection:
        repository = Repository(connection)
        controller = Controller(telegram_message_manager, repository)

        # iterate over the latest messages for update in updates:
        for update in updates:
            try:
                if "message" in update:
                    message = update["message"]
                    text = message["text"]

                    if text == "/newqueue":
                        controller.prompt_queue_name(message)
                    elif "reply_to_message" in message \
                        and message["reply_to_message"]["text"] \
                            == NEW_QUEUE_COMMAND_RESPONSE_TEXT:
                        controller.respond_to_prompted_queue_name(message)
                    elif text == "/addmetoqueue":
                        controller.handle_add_me_to_queue_command(message)
                    elif text == "/showqueue":
                        controller.handle_show_queue_command(message)
                    elif text == "/crossoutnext":
                        controller.handle_cross_out_next_command(message)
                    elif text == "/uncrossoutlast":
                        controller.handle_uncross_out_last_command(message)
                    elif text == "/removemefromqueue":
                        controller.handle_remove_me_from_queue_command(message)
                    else:
                        controller.echo_message(message)
                elif "callback_query" in update:
                    callback_query = update["callback_query"]
                    callback_query_data = json.loads(callback_query["data"])
                    callback_query_type = callback_query_data["type"]

                    if callback_query_type == ButtonCallbackType.NOOP:
                        controller.handle_noop_callback(callback_query)
                    elif callback_query_type == \
                            ButtonCallbackType.SHOW_NEXT_QUEUE_PAGE:
                        controller.handle_show_next_queue_page_callback(
                            callback_query,
                            callback_query_data
                        )
                    elif callback_query_type == \
                            ButtonCallbackType.SHOW_PREVIOUS_QUEUE_PAGE:
                        controller.handle_show_previous_queue_page_callback(
                            callback_query,
                            callback_query_data
                        )
                    elif callback_query_type == ButtonCallbackType.SHOW_QUEUE:
                        controller.handle_show_queue_callback(
                            callback_query,
                            callback_query_data
                        )
                    elif callback_query_type == \
                            ButtonCallbackType.ADD_ME_TO_QUEUE:
                        controller.handle_add_me_to_queue_callback(
                            callback_query,
                            callback_query_data
                        )
                    elif callback_query_type == \
                            ButtonCallbackType.CROSS_OUT_NEXT:
                        controller.handle_cross_out_next_callback(
                            callback_query,
                            callback_query_data
                        )
                    elif callback_query_type == \
                            ButtonCallbackType.UNCROSS_OUT_LAST:
                        controller.handle_uncross_out_last_callback(
                            callback_query,
                            callback_query_data
                        )
                    elif callback_query_type == \
                            ButtonCallbackType.REMOVE_ME_FROM_QUEUE:
                        controller.handle_remove_me_from_queue_callback(
                            callback_query,
                            callback_query_data
                        )
                    else:
                        print(
                            "Received an unknown callback query type: "
                            + callback_query_type
                        )
                        controller.handle_noop_callback(callback_query)
            except KeyboardInterrupt:
                exit()
            except HTTPError as http_error:
                print("Encountered an HTTP error")
                print("Stack trace:")
                print(traceback.format_exc())
                print("URL: " + http_error.url)
                print("Response: " + http_error.file.read().decode("UTF-8") +
                      "\n")
                controller.handle_error_while_processing_update(update)
            except Exception as error:
                print(traceback.format_exc())
                controller.handle_error_while_processing_update(update)
