class Repository:
    def __init__(self, connection):
        self.connection = connection
        self.cursor = connection.cursor()

    def create_schema(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS queues (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS pupils (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                queue_id INTEGER NOT NULL,
                FOREIGN KEY (queue_id)
                    REFERENCES queues (id)
                        ON DELETE CASCADE
                        ON UPDATE NO ACTION
            )
        """)

    def create_queue(self, queue_name):
        self.cursor.execute("""
            INSERT INTO queues (name)
            VALUES (?)
        """, (queue_name,))

    def commit(self):
        self.connection.commit()
