import sqlite3


def create_sqlite_connection(database_path):
    connection = sqlite3.connect(database_path)
    connection.cursor().execute("PRAGMA foreign_keys = ON")
    return connection
