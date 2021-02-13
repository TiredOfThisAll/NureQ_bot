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
            CREATE TABLE IF NOT EXISTS queue_members (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                user_first_name TEXT NOT NULL,
                user_last_name TEXT NULL,
                user_username TEXT NULL,
                queue_id INTEGER NOT NULL,
                crossed INTEGER DEFAULT 0 NOT NULL,
                FOREIGN KEY (queue_id)
                    REFERENCES queues (id)
                        ON DELETE CASCADE
                        ON UPDATE NO ACTION,
                UNIQUE(user_id, queue_id)
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

    def add_me_to_queue(
        self,
        user_id,
        user_first_name,
        user_last_name,
        user_username,
        queue_id
    ):
        try:
            self.cursor.execute("""
                INSERT INTO queue_members (
                    user_id,
                    user_first_name,
                    user_last_name,
                    user_username,
                    queue_id
                )
                VALUES (
                    :user_id,
                    :user_first_name,
                    :user_last_name,
                    :user_username,
                    :queue_id
                )
            """, {
                "user_id": user_id,
                "user_first_name": user_first_name,
                "user_last_name": user_last_name,
                "user_username": user_username,
                "queue_id": queue_id,
            })
        except sqlite3.IntegrityError:
            return "DUPLICATE_MEMBERS"

    def find_uncrossed_queue_member(self, queue_id):
        queue_member_tuple = self.cursor.execute("""
            SELECT *
            FROM queue_members
            WHERE crossed = 0 AND queue_id = ?
        """, (queue_id,)).fetchone()
        if queue_member_tuple is None:
            return None
        return QueueMember.from_tuple(queue_member_tuple)

    def find_last_crossed_queue_member(self, queue_id):
        queue_member_tuple = self.cursor.execute("""
            SELECT *
            FROM queue_members
            WHERE crossed = 1 AND queue_id = ?
            ORDER BY id DESC
            LIMIT 1
        """, (queue_id,)).fetchone()
        if queue_member_tuple is None:
            return None
        return QueueMember.from_tuple(queue_member_tuple)

    def cross_out_queue_member(self, user_id, queue_id):
        self.cursor.execute("""
            UPDATE queue_members
            SET crossed = 1
            WHERE user_id = ? AND queue_id = ?
        """, (user_id, queue_id))

    def uncross_out_the_queue_member(self, user_id, queue_id):
        self.cursor.execute("""
            UPDATE queue_members
            SET crossed = 0
            WHERE user_id = ? AND queue_id = ?
        """, (user_id, queue_id))

    def remove_user_from_queue(self, name, queue_id):
        self.cursor.execute("""
            DELETE FROM queue_members
            WHERE queue_id = ? AND name = ?
        """, (queue_id, name))
        return self.cursor.rowcount == 1

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
            FROM queue_members
            WHERE queue_id = ?
        """, (queue_id,)).fetchall()
        return list(map(QueueMember.from_tuple, queue_member_tuples))

    def get_queue_name_by_queue_id(self, queue_id):
        queue_name_tuple = self.cursor.execute("""
            SELECT name
            FROM queues
            WHERE id = ?
        """, (queue_id,)).fetchone()
        if queue_name_tuple is None:
            return None
        return queue_name_tuple[0]

    def commit(self):
        self.connection.commit()
