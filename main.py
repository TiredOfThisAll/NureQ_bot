import time
from os import path
import sqlite3

from repository import Repository
from telegram_message_manager import TelegramMessageManager
from controller import Controller

# constants
TELEGRAM_BOT_API_URL = "https://api.telegram.org/bot"
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
    updates = telegram_message_manager.get_latest_messages()

    with sqlite3.connect(DATABASE_NAME) as connection:
        repository = Repository(connection)
        controller = Controller(telegram_message_manager, repository)

        # iterate over the latest messages
        for update in updates:
            if "message" in update:
                message = update["message"]
                text = message["text"]

                if text == "/newqueue":
                    controller.prompt_queue_name(message)
                else:
                    if "reply_to_message" in message \
                        and message["reply_to_message"]["text"] \
                            == NEW_QUEUE_COMMAND_RESPONSE_TEXT:
                        controller.respond_to_prompted_queue_name(message)
                    else:
                        controller.echo_message(message)

    time.sleep(1)
