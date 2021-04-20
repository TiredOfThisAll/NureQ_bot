from datetime import datetime


class Log:
    def __init__(self, id, level, timestamp, message):
        self.id = id
        self.level = level
        self.timestamp = datetime.fromisoformat(timestamp)
        self.message = message

    def from_tuple(source):
        return Log(*source)

    def get_formatted_timestamp(self):
        return self.timestamp.strftime("%Y.%m.%d %H:%M:%S")
