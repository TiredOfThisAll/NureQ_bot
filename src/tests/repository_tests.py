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
