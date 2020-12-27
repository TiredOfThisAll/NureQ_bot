from urllib.request import urlopen
from urllib.parse import urlencode
import json

TELEGRAM_BOT_API_URL = "https://api.telegram.org/bot"


class TelegramMessageManager:
    def __init__(self, offset, token):
        self.offset = offset
        self.token = token

    def get_latest_messages(self):
        get_updates_url = TELEGRAM_BOT_API_URL + self.token + "/getUpdates"
        if self.offset is not None:
            get_updates_url += "?offset=" + str(self.offset)
        with urlopen(get_updates_url) as response:
            response_string = response.read().decode("utf-8")
        response_object = json.loads(response_string)
        return response_object["result"]

    def send_message(self, chat_id, response_text):
        send_message_url = TELEGRAM_BOT_API_URL + self.token + "/sendMessage?" \
                            + urlencode({
                                "chat_id": chat_id,
                                "text": response_text
                            })
        with urlopen(send_message_url):
            pass

    def set_bot_commands(self, bot_commands_file):
        bot_commands = json.dumps(json.loads(bot_commands_file.read()))
        with urlopen(TELEGRAM_BOT_API_URL + self.token + "/setMyCommands?" \
                     + urlencode({"commands": bot_commands})):
            pass
