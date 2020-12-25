from urllib.request import urlopen
from urllib.parse import urlencode
import time
from os import path
import json
import sqlite3

from repository import Repository

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

# notify Telegram about supported commands
with open("bot_commands.json") as bot_commands_file:
    bot_commands = json.dumps(json.loads(bot_commands_file.read()))
with urlopen(TELEGRAM_BOT_API_URL + token + "/setMyCommands?" \
    + urlencode({ "commands": bot_commands })):
    pass

# create DB schema if it doesn't exist yet
with sqlite3.connect(DATABASE_NAME) as connection:
    repository = Repository(connection)
    repository.create_schema()
    repository.commit()

# the 'game' loop that listens for new messages and responds to them
offset = None
while True:
    # get latest messages
    get_updates_url = TELEGRAM_BOT_API_URL + token + "/getUpdates"
    if offset is not None:
        get_updates_url += "?offset=" + str(offset)
    with urlopen(get_updates_url) as response:
        response_string = response.read().decode("utf-8")
    response_object = json.loads(response_string)
    updates = response_object["result"]

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
                    send_message_url = TELEGRAM_BOT_API_URL + token \
                        + "/sendMessage?" \
                        + urlencode({
                            "chat_id": chat_id,
                            "text": response_text
                        })
                    with urlopen(send_message_url):
                        pass
                else:
                    if "reply_to_message" in message and message["reply_to_message"]["text"] == NEW_QUEUE_COMMAND_RESPONSE_TEXT:
                        repository.create_queue(text)
                        repository.commit()
                        response_text = "Создана новая очередь: " + text
                        send_message_url = TELEGRAM_BOT_API_URL + token \
                            + "/sendMessage?" \
                            + urlencode({
                                "chat_id": chat_id,
                                "text": response_text
                            })
                        with urlopen(send_message_url):
                            pass
                    else:
                        response_text = text
                        send_message_url = TELEGRAM_BOT_API_URL + token \
                            + "/sendMessage?" \
                            + urlencode({
                                "chat_id": chat_id,
                                "text": response_text
                            })
                        with urlopen(send_message_url):
                            pass

    time.sleep(1)

