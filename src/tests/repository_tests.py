import sqlite3
import unittest

from data_access.repository import Repository


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.repository = Repository(self.connection)
        self.repository.create_schema()

    def tearDown(self):
        self.connection.close()

    def generate_queue_member_test_data(self):
        self.connection.execute("""
            INSERT INTO queue_members (
                user_id,
                user_first_name,
                user_last_name,
                user_username,
                queue_id,
                position
            )
            VALUES
                (1, 'John', 'Doe', 'johndoe', 1, 0),
                (2, 'Mary', 'Smith', 'marysmith', 1, 1),
                (3, 'William', 'Turner', 'willturner', 1, 2)
        """)

    def test_remove_user_from_queue_returns_false(self):
        self.generate_queue_member_test_data()

        successful = self.repository.remove_user_from_queue(100, 100)

        self.assertFalse(successful)

    def test_remove_user_from_queue_returns_true(self):
        self.generate_queue_member_test_data()

        successful = self.repository.remove_user_from_queue(2, 1)

        self.assertTrue(successful)

    def test_remove_user_from_queue_recalculates_positions(self):
        user_id = 2
        queue_id = 1
        self.generate_queue_member_test_data()

        self.repository.remove_user_from_queue(user_id, queue_id)

        position_tuples = self.connection.execute("""
            SELECT position
            FROM queue_members
            WHERE queue_id = ?
            ORDER BY position
        """, (queue_id,)).fetchall()
        self.assertEqual(position_tuples, [(0,), (1,)])

    def test_move_queue_member(self):
        queue_id = 1
        dragged_queue_member_position = 0
        drop_queue_member_position = 2
        self.generate_queue_member_test_data()

        self.repository.move_queue_member(
            queue_id,
            dragged_queue_member_position,
            drop_queue_member_position
        )
        position_tuples = self.connection.execute("""
            SELECT user_id, position
            FROM queue_members
            WHERE queue_id = ?
            ORDER BY position
        """, (queue_id,)).fetchall()
        self.assertEqual(position_tuples, [(2, 0), (3, 1), (1, 2)])

    def test_swap_positions(self):
        queue_id = 1
        first_queue_member_position = 0
        second_queue_member_position = 1
        self.generate_queue_member_test_data()

        self.repository.swap_positions(
            queue_id,
            first_queue_member_position,
            second_queue_member_position
        )

        position_tuples = self.connection.execute("""
            SELECT user_id, position
            FROM queue_members
            WHERE queue_id = ?
            ORDER BY position
        """, (queue_id,)).fetchall()
        self.assertEqual(position_tuples, [(2, 0), (1, 1), (3, 2)])
