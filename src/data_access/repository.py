import sqlite3
from datetime import datetime

from data_access.models.queue import Queue
from data_access.models.queue_member import QueueMember


class Repository:
    def __init__(self, connection):
        self.connection = connection
        self.cursor = connection.cursor()

    def create_schema(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS queues (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                last_updated_on TEXT NOT NULL
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
                INSERT INTO queues (name, last_updated_on)
                VALUES (?, ?)
            """, (queue_name, datetime.utcnow()))
        except sqlite3.IntegrityError as integrity_error:
            if str(integrity_error) == "UNIQUE constraint failed: queues.name":
                return "QUEUE_NAME_DUPLICATE"
            if str(integrity_error) == \
                    "NOT NULL constraint failed: queues.name":
                return "NOT_NULL_CONSTRAINT_FAILED"
            raise integrity_error

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

    def remove_user_from_queue(self, user_id, queue_id):
        self.cursor.execute("""
            DELETE FROM queue_members
            WHERE queue_id = ? AND user_id = ?
        """, (queue_id, user_id))
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
            ORDER BY datetime(last_updated_on) DESC
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

    def refresh_queues_last_time_updated_on(self, queue_id):
        self.cursor.execute("""
            UPDATE queues
            SET last_updated_on = ?
            WHERE id = ?
        """, (datetime.utcnow(), queue_id))

    def commit(self):
        self.connection.commit()
