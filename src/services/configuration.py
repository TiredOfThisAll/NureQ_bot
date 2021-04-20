import json
from os import path

PROJECT_PATH = path.abspath(path.join(__file__, "..", "..", ".."))


class Configuration:
    def load():
        config_file_path = path.join(
            PROJECT_PATH,
            "config",
            "configuration.json"
        )
        with open(config_file_path) as configuration_file:
            configuration_dict = json.loads(configuration_file.read())

        token_path = path.join(PROJECT_PATH, configuration_dict["token"])
        # load the token if available
        if not path.exists(token_path):
            print(f"You need the token file at {token_path}")
            exit(1)

        configuration = Configuration()

        with open(token_path) as token_file:
            token = token_file.readline()
            if token[-1] == "\n":
                token = token[:-1]
            configuration.TOKEN = token

        configuration.DATABASE_PATH \
            = path.join(PROJECT_PATH, configuration_dict["database"])
        configuration.LOGS_PATH \
            = path.join(PROJECT_PATH, configuration_dict["logs"])
        configuration.PAUSE_DURATION = configuration_dict["pause"]
        configuration.QUEUE_NAME_LIMIT = configuration_dict["queue_name_limit"]
        configuration.BOT_USERNAME = configuration_dict["bot_username"]

        bot_commands_file_path \
            = path.join(PROJECT_PATH, "config", "bot_commands.json")
        with open(bot_commands_file_path, encoding="UTF-8") \
                as bot_commands_file:
            configuration.BOT_COMMANDS = json.loads(bot_commands_file.read())

        return configuration


CONFIGURATION = Configuration.load()
