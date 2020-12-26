from urllib.request import urlopen
from urllib.parse import urlencode
from os import path
import json

TELEGRAM_BOT_API_URL = "https://api.telegram.org/bot"
TOKEN_FILE_NAME = "token"

with open(TOKEN_FILE_NAME) as token_file:
    token = token_file.readline()
    if token[-1] == "\n":
        token = token[:-1]


class TelegramMessageManager:
    def __init__(self, offset):
        self.offset = offset

    def get_latest_messages(self):
        get_updates_url = TELEGRAM_BOT_API_URL + token + "/getUpdates"
        if self.offset is not None:
            get_updates_url += "?offset=" + str(self.offset)
        with urlopen(get_updates_url) as response:
            response_string = response.read().decode("utf-8")
        response_object = json.loads(response_string)
        return response_object["result"]

    @staticmethod
    def send_message(chat_id, response_text):
        send_message_url = TELEGRAM_BOT_API_URL + token + "/sendMessage?" \
                            + urlencode({
                                "chat_id": chat_id,
                                "text": response_text
                            })
        with urlopen(send_message_url):
            pass

    @staticmethod
    def set_bot_commands():
        with open("bot_commands.json") as bot_commands_file:
            bot_commands = json.dumps(json.loads(bot_commands_file.read()))
        with urlopen(TELEGRAM_BOT_API_URL + token + "/setMyCommands?" \
                     + urlencode({"commands": bot_commands})):
            pass
