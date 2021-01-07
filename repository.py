import sqlite3
from models.queue import Queue
from models.queue_member import QueueMember


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
        queue_id_tuple = self.cursor.execute("""
            SELECT id
            FROM queues
            WHERE name = ?
            LIMIT 1
        """, (queue_name,)).fetchone()
        if queue_id_tuple is None:
            return "NO_QUEUE"
        queue_id = queue_id_tuple[0]

        try:
            self.cursor.execute("""
                INSERT INTO pupils (name, queue_id)
                VALUES (?, ?)
            """, (name, queue_id))
        except sqlite3.IntegrityError:
            return "DUPLICATE_MEMBERS"

    def get_total_queue_count(self):
        return self.cursor.execute("""
            SELECT COUNT(*)
            FROM queues
        """).fetchone()[0]

    def get_queues_page(self, page_index, page_size):
        skip_amount = (page_index - 1) * page_size
        queue_tuples = self.cursor.execute("""
            SELECT *
            FROM queues
            LIMIT ?, ?
        """, (skip_amount, page_size)).fetchall()
        return list(map(Queue.from_tuple, queue_tuples))

    def get_queue_members_by_queue_id(self, queue_id):
        queue_member_tuples = self.cursor.execute("""
            SELECT *
            FROM pupils
            WHERE queue_id = ?
        """, (queue_id,)).fetchall()
        return list(map(QueueMember.from_tuple, queue_member_tuples))

    def get_queue_name_by_queue_id(self, queue_id):
        return self.cursor.execute("""
            SELECT name
            FROM queues
            WHERE id = ?
        """, (queue_id,)).fetchone()[0]

    def commit(self):
        self.connection.commit()
