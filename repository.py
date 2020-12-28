import sqlite3


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
        try:
            self.cursor.execute("""
                INSERT INTO queues (name)
                VALUES (?)
            """, (queue_name,))
        except sqlite3.IntegrityError as integrity_error:
            return "INTEGRITY_ERROR"

    def add_me_to_queue(self, name, queue_name):
        self.cursor.execute("""
            SELECT id
            FROM queues
            WHERE name =?
            LIMIT 1
        """, (queue_name,))
        queue_id = str(self.cursor.fetchone())
        self.cursor.execute("""
            INSERT INTO pupils (name, queue_id)
            VALUES (?, ?)
        """, (name, queue_id))

    def commit(self):
        self.connection.commit()
