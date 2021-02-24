from urllib.request import urlopen
from urllib.parse import urlencode
import json

TELEGRAM_BOT_API_URL = "https://api.telegram.org/bot"


class TelegramMessageManager:
    def __init__(self, token):
        self.token = token
        self.offset = None

    def get_latest_messages(self):
        get_updates_url = TELEGRAM_BOT_API_URL + self.token + "/getUpdates"
        if self.offset is not None:
            get_updates_url += "?offset=" + str(self.offset)

        with urlopen(get_updates_url) as response:
            response_string = response.read().decode("utf-8")
        updates = json.loads(response_string)["result"]

        if len(updates) != 0:
            max_update_id = max(
                map(lambda update: update["update_id"], updates)
            )
            if self.offset is None or max_update_id >= self.offset:
                self.offset = max_update_id + 1

        return updates

    def send_message(
        self,
        chat_id,
        response_text,
        reply_markup=None,
        parse_mode=None,
        entities=None
    ):
        query_parameters = {
            "chat_id": chat_id,
            "text": response_text,
        }
        if parse_mode is not None:
            query_parameters["parse_mode"] = parse_mode
        if reply_markup is not None:
            query_parameters["reply_markup"] = json.dumps(reply_markup)
        if entities is not None:
            query_parameters["entities"] = json.dumps(entities)
        send_message_url = TELEGRAM_BOT_API_URL + self.token \
            + "/sendMessage?" + urlencode(query_parameters)
        with urlopen(send_message_url):
            pass

    def set_bot_commands(self, bot_commands):
        set_bot_commands_url = TELEGRAM_BOT_API_URL + self.token \
            + "/setMyCommands?" + urlencode({"commands": bot_commands})
        with urlopen(set_bot_commands_url):
            pass

    def answer_callback_query(self, callback_query_id):
        target_url = TELEGRAM_BOT_API_URL + self.token \
            + "/answerCallbackQuery?" + urlencode({
                "callback_query_id": str(callback_query_id)
            })
        with urlopen(target_url):
            pass

    def edit_message_reply_markup(self, chat_id, message_id, reply_markup):
        target_url = TELEGRAM_BOT_API_URL + self.token \
            + "/editMessageReplyMarkup?" + urlencode({
                "chat_id": chat_id,
                "message_id": message_id,
                "reply_markup": json.dumps(reply_markup),
            })
        with urlopen(target_url):
            pass
