class Queue:
    def __init__(self, id, name):
        self.id = id
        self.name = name

    def from_tuple(queue_tuple):
        return Queue(queue_tuple[0], queue_tuple[1])

    def __str__(self):
        return f"Queue: id = {self.id}, name = {self.name}"
