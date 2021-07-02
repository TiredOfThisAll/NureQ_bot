import sqlite3
from datetime import datetime

from data_access.models.queue import Queue
from data_access.models.queue_member import QueueMember
from data_access.models.log import Log
from web.models.queue_view import QueueView


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
                position INTEGER NOT NULL,
                FOREIGN KEY (queue_id)
                    REFERENCES queues (id)
                        ON DELETE CASCADE
                        ON UPDATE NO ACTION,
                UNIQUE (user_id, queue_id),
                UNIQUE (position, queue_id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY,
                level TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                message TEXT NOT NULL
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
                    queue_id,
                    position
                )
                VALUES (
                    :user_id,
                    :user_first_name,
                    :user_last_name,
                    :user_username,
                    :queue_id,
                    (
                        SELECT IFNULL(MAX(position) + 1, 0)
                        FROM queue_members
                        WHERE queue_id = :queue_id
                    )
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
            ORDER BY position
            LIMIT 1
        """, (queue_id,)).fetchone()
        if queue_member_tuple is None:
            return None
        return QueueMember.from_tuple(queue_member_tuple)

    def find_last_crossed_queue_member(self, queue_id):
        queue_member_tuple = self.cursor.execute("""
            SELECT *
            FROM queue_members
            WHERE crossed = 1 AND queue_id = ?
            ORDER BY position DESC
            LIMIT 1
        """, (queue_id,)).fetchone()
        if queue_member_tuple is None:
            return None
        return QueueMember.from_tuple(queue_member_tuple)

    def cross_out_queue_member(self, user_id, queue_id):
        self.set_queue_member_crossed_out(user_id, queue_id, 1)

    def uncross_out_the_queue_member(self, user_id, queue_id):
        self.set_queue_member_crossed_out(user_id, queue_id, 0)

    def set_queue_member_crossed_out(self, user_id, queue_id, crossed_out):
        self.cursor.execute("""
            UPDATE queue_members
            SET crossed = ?
            WHERE user_id = ? AND queue_id = ?
        """, (crossed_out, user_id, queue_id))

    # returns True if the member to remove was found and False otherwise
    def remove_user_from_queue(self, user_id, queue_id):
        # get position of the member that we are removing
        position_tuple_or_none = self.cursor.execute("""
            SELECT position
            FROM queue_members
            WHERE queue_id = ? AND user_id = ?
        """, (queue_id, user_id)).fetchone()
        if position_tuple_or_none is None:
            return False
        position = position_tuple_or_none[0]

        # remove the member from queue
        self.cursor.execute("""
            DELETE FROM queue_members
            WHERE queue_id = ? AND user_id = ?
        """, (queue_id, user_id))

        # update all affected queue member positions
        self.cursor.execute("""
            UPDATE queue_members
            SET position = position - 1
            WHERE queue_id = ? AND position > ?
        """, (queue_id, position))

        return True

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
            ORDER BY position
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

    def get_queue_page_view(self, page_index, page_size):
        skip_amount = (page_index - 1) * page_size
        queue_tuples = self.cursor.execute("""
            SELECT queues.id, queues.name, queues.last_updated_on,
                COUNT(queue_members.id)
            FROM queues
            LEFT JOIN queue_members ON queues.id == queue_members.queue_id
            GROUP BY queues.id, queues.name, queues.last_updated_on
            ORDER BY datetime(queues.last_updated_on) DESC
        """).fetchall()
        # TODO: pagination
        return list(map(QueueView.from_tuple, queue_tuples))

    def get_queue_by_id(self, id):
        queue_tuple = self.cursor.execute("""
            SELECT *
            FROM queues
            WHERE id = ?
        """, (id,)).fetchone()
        if not queue_tuple:
            return None
        return Queue.from_tuple(queue_tuple)

    def move_up_queue_member(self, queue_id, position):
        return self.swap_positions(queue_id, position, position - 1)

    def move_down_queue_member(self, queue_id, position):
        return self.swap_positions(queue_id, position, position + 1)

    def swap_positions(self, queue_id, pos_1, pos_2):
        # Validate positions
        if pos_1 < 0 or pos_2 < 0 or pos_1 == pos_2:
            return "INVALID_POSITION"
        queue_size = self.cursor.execute("""
            SELECT COUNT(*)
            FROM queue_members
            WHERE queue_id = ?
        """, (queue_id,)).fetchone()[0]
        if pos_1 >= queue_size or pos_2 >= queue_size:
            return "INVALID_POSITION"

        self.cursor.execute("""
            UPDATE queue_members
            SET position = CASE position
                WHEN :pos_1 THEN -:pos_2
                WHEN :pos_2 THEN -:pos_1
            END
            WHERE queue_id = :queue_id AND position IN (:pos_1, :pos_2)
        """, {
            "queue_id": queue_id,
            "pos_1": pos_1,
            "pos_2": pos_2
        })
        self.cursor.execute("""
            UPDATE queue_members
            SET position = -position
            WHERE position < 0
        """)

    def move_queue_member(
            self,
            queue_id,
            user_id_1,
            user_id_2,
            inserted_before
    ):
        positions = self.cursor.execute(f"""
            SELECT user_id, position
            FROM queue_members
            WHERE queue_id = ? AND user_id IN (?, ?)
        """, (queue_id, user_id_1, user_id_2)).fetchall()

        if len(positions) != 2:
            return "INVALID_USER_ID"

        moved_from_position = next(
            position for user_id, position in positions if user_id == user_id_1
        )
        target_position = next(
            position for user_id, position in positions if user_id == user_id_2
        )

        moved_down = target_position > moved_from_position

        target_position += int(not moved_down) * int(not inserted_before) \
            - int(moved_down) * int(inserted_before)

        self.cursor.execute("""
            UPDATE queue_members
            SET position = CASE position
                WHEN :moved_from_position THEN -:target_position
                ELSE -(position + :offset_for_others)
            END
            WHERE queue_id = :queue_id AND
            position BETWEEN MIN(:moved_from_position, :target_position)
            AND MAX(:moved_from_position, :target_position)
        """, {
            "moved_from_position": moved_from_position,
            "target_position": target_position,
            "queue_id": queue_id,
            "offset_for_others":
                1 if moved_from_position > target_position else -1
        })

        self.cursor.execute("""
            UPDATE queue_members
            SET position = -position
            WHERE position < 0
        """)

    def delete_queue(self, queue_id):
        self.cursor.execute("""
            DELETE FROM queues
            WHERE id = ?
        """, (queue_id,))

    def is_user_admin(self, user_id):
        tuple_user_id = self.cursor.execute("""
            SELECT user_id
            FROM admins
            WHERE user_id = ?
        """, (user_id,)).fetchone()
        return tuple_user_id is not None

    def rename_queue(self, id, new_name):
        try:
            self.cursor.execute("""
                UPDATE queues
                SET name = ?
                WHERE id = ?
            """, (new_name, id))
        except sqlite3.IntegrityError:
            return "QUEUE_NAME_DUPLICATE"

    def get_all_logs(self):
        log_tuples = self.cursor.execute("""
            SELECT *
            FROM logs
            ORDER BY datetime(timestamp) DESC
        """).fetchall()
        return list(map(Log.from_tuple, log_tuples))

    def commit(self):
        self.connection.commit()
