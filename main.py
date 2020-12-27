import time
from os import path

import sqlite3

from repository import Repository
from telegram_message_manager import TelegramMessageManager

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


with open("bot_commands.json") as bot_commands_file:
    telegram_message_manager = TelegramMessageManager(None, token)
    telegram_message_manager.set_bot_commands(bot_commands_file)

# create DB schema if it doesn't exist yet
with sqlite3.connect(DATABASE_NAME) as connection:
    repository = Repository(connection)
    repository.create_schema()
    repository.commit()

# the 'game' loop that listens for new messages and responds to them
offset = None
while True:

    telegram_message_manager = TelegramMessageManager(offset, token)
    updates = telegram_message_manager.get_latest_messages()

    with sqlite3.connect(DATABASE_NAME) as connection:
        repository = Repository(connection)
        # iterate over the latest messages
        for update in updates:
            if offset is None or update["update_id"] >= offset:
                offset = update["update_id"] + 1

            if "message" in update:
                message = update["message"]
                chat_id = message["chat"]["id"]
                text = message["text"]

                if text == "/newqueue":
                    response_text = NEW_QUEUE_COMMAND_RESPONSE_TEXT
                    TelegramMessageManager.send_message(chat_id, response_text)
                else:
                    if "reply_to_message" in message and message["reply_to_message"]["text"] == NEW_QUEUE_COMMAND_RESPONSE_TEXT:
                        repository.create_queue(text)
                        repository.commit()
                        response_text = "Создана новая очередь: " + text
                        telegram_message_manager.send_message(chat_id, response_text)
                    else:
                        response_text = text
                        telegram_message_manager.send_message(chat_id, response_text)

    time.sleep(1)
