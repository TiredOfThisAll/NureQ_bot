from urllib.request import urlopen
import time
from os import path
import json

# constants
TELEGRAM_BOT_API_URL = "https://api.telegram.org/bot"
TOKEN_FILE_NAME = "token"
SLEEP_DURATION_IN_SECONDS = 1

# load the token if available
if not path.exists(TOKEN_FILE_NAME):
    print("You need the token file")
    exit(1)

with open(TOKEN_FILE_NAME) as token_file:
    token = token_file.readline()[:-1] # drop the final '\n' character

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
        send_message_url = TELEGRAM_BOT_API_URL + token \
            + "/sendMessage?chat_id=" + str(chat_id) + "&text=" + text
        with urlopen(send_message_url) as response:
            pass

    time.sleep(SLEEP_DURATION_IN_SECONDS)

