from urllib.request import urlopen
from urllib.parse import urlencode
import time
from os import path
import json

# constants
TELEGRAM_BOT_API_URL = "https://api.telegram.org/bot"
TOKEN_FILE_NAME = "token"

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

    # iterate over the latest messages
    for update in updates:
        if offset is None or update["update_id"] >= offset:
            offset = update["update_id"] + 1
        chat_id = update["message"]["chat"]["id"]
        text = update["message"]["text"]
        send_message_url = TELEGRAM_BOT_API_URL + token + "/sendMessage?" \
            + urlencode({ "chat_id": chat_id, "text": text })
        with urlopen(send_message_url):
            pass

    time.sleep(1)

