import sqlite3
import unittest

from data_access.repository import Repository


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        # we don't need to check foreign key constraints in tests,
        # hence no PRAGMA command
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

    def test_move_queue_member_down_above(self):
        self.generate_queue_member_test_data()
        queue_id = 1

        error = self.repository.move_queue_member(
            queue_id,
            user_id_1=1,
            user_id_2=3,
            inserted_before=True
        )

        self.assertIsNone(error)
        position_tuples = self.connection.execute("""
            SELECT user_id, position
            FROM queue_members
            WHERE queue_id = ?
            ORDER BY position
        """, (queue_id,)).fetchall()
        self.assertEqual(position_tuples, [(2, 0), (1, 1), (3, 2)])

    def test_move_queue_member_down_below(self):
        self.generate_queue_member_test_data()
        queue_id = 1

        error = self.repository.move_queue_member(
            queue_id,
            user_id_1=1,
            user_id_2=3,
            inserted_before=False
        )

        self.assertIsNone(error)
        position_tuples = self.connection.execute("""
            SELECT user_id, position
            FROM queue_members
            WHERE queue_id = ?
            ORDER BY position
        """, (queue_id,)).fetchall()
        self.assertEqual(position_tuples, [(2, 0), (3, 1), (1, 2)])

    def test_move_queue_member_up_above(self):
        self.generate_queue_member_test_data()
        queue_id = 1

        error = self.repository.move_queue_member(
            queue_id,
            user_id_1=3,
            user_id_2=1,
            inserted_before=True
        )

        self.assertIsNone(error)
        position_tuples = self.connection.execute("""
            SELECT user_id, position
            FROM queue_members
            WHERE queue_id = ?
            ORDER BY position
        """, (queue_id,)).fetchall()
        self.assertEqual(position_tuples, [(3, 0), (1, 1), (2, 2)])

    def test_move_queue_member_up_below(self):
        self.generate_queue_member_test_data()
        queue_id = 1

        error = self.repository.move_queue_member(
            queue_id,
            user_id_1=3,
            user_id_2=1,
            inserted_before=False
        )

        self.assertIsNone(error)
        position_tuples = self.connection.execute("""
            SELECT user_id, position
            FROM queue_members
            WHERE queue_id = ?
            ORDER BY position
        """, (queue_id,)).fetchall()
        self.assertEqual(position_tuples, [(1, 0), (3, 1), (2, 2)])

    def test_move_queue_member_to_same_position_from_below(self):
        self.generate_queue_member_test_data()
        queue_id = 1

        error = self.repository.move_queue_member(
            queue_id,
            user_id_1=2,
            user_id_2=1,
            inserted_before=False
        )

        self.assertIsNone(error)
        position_tuples = self.connection.execute("""
            SELECT user_id, position
            FROM queue_members
            WHERE queue_id = ?
            ORDER BY position
        """, (queue_id,)).fetchall()
        self.assertEqual(position_tuples, [(1, 0), (2, 1), (3, 2)])

    def test_move_queue_member_to_same_position_from_above(self):
        self.generate_queue_member_test_data()
        queue_id = 1

        error = self.repository.move_queue_member(
            queue_id,
            user_id_1=1,
            user_id_2=2,
            inserted_before=True
        )

        self.assertIsNone(error)
        position_tuples = self.connection.execute("""
            SELECT user_id, position
            FROM queue_members
            WHERE queue_id = ?
            ORDER BY position
        """, (queue_id,)).fetchall()
        self.assertEqual(position_tuples, [(1, 0), (2, 1), (3, 2)])

    def test_move_queue_member_double_move_first_member(self):
        self.generate_queue_member_test_data()
        queue_id = 1

        error = self.repository.move_queue_member(
            queue_id,
            user_id_1=2,
            user_id_2=1,
            inserted_before=True
        )
        self.assertIsNone(error)

        error = self.repository.move_queue_member(
            queue_id,
            user_id_1=1,
            user_id_2=2,
            inserted_before=True
        )
        self.assertIsNone(error)

        position_tuples = self.connection.execute("""
            SELECT user_id, position
            FROM queue_members
            WHERE queue_id = ?
            ORDER BY position
        """, (queue_id,)).fetchall()
        self.assertEqual(position_tuples, [(1, 0), (2, 1), (3, 2)])

    def test_move_queue_member_invalid_queue_id(self):
        self.generate_queue_member_test_data()

        error = self.repository.move_queue_member(
            queue_id=-1,
            user_id_1=1,
            user_id_2=3,
            inserted_before=True
        )

        self.assertEqual(error, "INVALID_QUEUE_OR_USER_ID")

    def test_move_queue_member_invalid_user_id_1(self):
        self.generate_queue_member_test_data()

        error = self.repository.move_queue_member(
            queue_id=1,
            user_id_1=-1,
            user_id_2=3,
            inserted_before=True
        )

        self.assertEqual(error, "INVALID_QUEUE_OR_USER_ID")

    def test_move_queue_member_invalid_user_id_2(self):
        self.generate_queue_member_test_data()

        error = self.repository.move_queue_member(
            queue_id=1,
            user_id_1=1,
            user_id_2=-1,
            inserted_before=True
        )

        self.assertEqual(error, "INVALID_QUEUE_OR_USER_ID")

    def test_move_queue_member_same_user_id(self):
        self.generate_queue_member_test_data()

        error = self.repository.move_queue_member(
            queue_id=1,
            user_id_1=1,
            user_id_2=1,
            inserted_before=True
        )

        self.assertEqual(error, "INVALID_QUEUE_OR_USER_ID")

    def test_swap_positions_double_swap_first_member(self):
        self.generate_queue_member_test_data()
        queue_id = 1
        first_queue_member_position = 0
        second_queue_member_position = 1

        error = self.repository.swap_positions(
            queue_id,
            first_queue_member_position,
            second_queue_member_position
        )
        self.assertIsNone(error)

        error = self.repository.swap_positions(
            queue_id,
            first_queue_member_position,
            second_queue_member_position
        )
        self.assertIsNone(error)

        position_tuples = self.connection.execute("""
            SELECT user_id, position
            FROM queue_members
            WHERE queue_id = ?
            ORDER BY position
        """, (queue_id,)).fetchall()
        self.assertEqual(position_tuples, [(1, 0), (2, 1), (3, 2)])
