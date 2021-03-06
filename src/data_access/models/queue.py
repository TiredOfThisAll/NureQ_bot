from datetime import datetime

class Queue:
    def __init__(self, id, name, last_updated_on):
        self.id = id
        self.name = name
        self.last_updated_on = last_updated_on

    def from_tuple(queue_tuple):
        return Queue(queue_tuple[0], queue_tuple[1], queue_tuple[2])

    def get_formatted_last_updated_on(self):
        return datetime.fromisoformat(self.last_updated_on) \
            .strftime("%d.%m.%Y %H:%M")

    def __str__(self):
        return "Queue: " \
            + f"id = {self.id}, " \
            + f"name = {self.name}, " \
            + f"last_updated_on = {self.last_updated_on}"
