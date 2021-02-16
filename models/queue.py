from datetime import datetime


class Queue:
    def __init__(self, id, name, last_updated_on):
        self.id = id
        self.name = name
        self.last_updated_on = last_updated_on
        self.parsed_last_update_on = datetime.fromisoformat(last_updated_on)

    def from_tuple(queue_tuple):
        return Queue(queue_tuple[0], queue_tuple[1], queue_tuple[2])

    def __str__(self):
        return f"Queue: id = {self.id}, name = {self.name}"
