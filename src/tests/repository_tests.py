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
