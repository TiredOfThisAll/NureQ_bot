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
                name TEXT NOT NULL,
                queue_id INTEGER NOT NULL,
                FOREIGN KEY (queue_id)
                    REFERENCES queues (id)
                        ON DELETE CASCADE
                        ON UPDATE NO ACTION,
                UNIQUE(name, queue_id)
            )
        """)

    def create_queue(self, queue_name):
        try:
            self.cursor.execute("""
                INSERT INTO queues (name)
                VALUES (?)
            """, (queue_name,))
        except sqlite3.IntegrityError:
            return "INTEGRITY_ERROR"

    def add_me_to_queue(self, name, queue_name):
        self.cursor.execute("""
            SELECT id
            FROM queues
            WHERE name =?
            LIMIT 1
        """, (queue_name,))
        queue_id_tuple = self.cursor.fetchone()
        if queue_id_tuple is None:
            return "Данной очереди не существует "
        queue_id = queue_id_tuple[0]

        try:
            self.cursor.execute("""
                INSERT INTO pupils (name, queue_id)
                VALUES (?, ?)
            """, (name, queue_id))
        except sqlite3.IntegrityError:
            return "Вы уже состоите в данной очереди "

    def commit(self):
        self.connection.commit()
