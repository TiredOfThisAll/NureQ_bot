from datetime import datetime
from services.dates import format_datetime


class QueueView:
    def __init__(self, id, name, last_updated_on, number_of_members, chat_id):
        self.id = id
        self.name = name
        self.last_updated_on = last_updated_on
        self.number_of_members = number_of_members
        self.chat_id = chat_id

    def from_tuple(queue_tuple):
        return QueueView(*queue_tuple)

    def get_formatted_last_updated_on(self):
        return format_datetime(datetime.fromisoformat(self.last_updated_on))
