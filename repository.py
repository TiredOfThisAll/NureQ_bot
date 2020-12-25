class Repository:
    def __init__(self, connection):
        self.connection = connection
        self.cursor = connection.cursor()

    def create_schema(self):
        pass

    def create_queue(self, queue_name):
        pass

    def commit(self):
        pass

