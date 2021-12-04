from datetime import datetime


class Queue:
    def __init__(self, id, name, last_updated_on, chat_id):
        self.id = id
        self.name = name
        self.last_updated_on = last_updated_on
        self.chat_id = chat_id

    def from_tuple(queue_tuple):
        return Queue(*queue_tuple)

    def get_formatted_last_updated_on(self):
        return datetime.fromisoformat(self.last_updated_on) \
            .strftime("%d.%m.%Y %H:%M")

    def __str__(self):
        return "Queue: " \
            + f"id = {self.id}, " \
            + f"name = {self.name}, " \
            + f"last_updated_on = {self.last_updated_on}"
