echo "
  PRAGMA foreign_keys = ON;

  DELETE FROM queues;

  INSERT INTO queues (name, last_updated_on)
  VALUES
    ('first', date('now')),
    ('second', date('now')),
    ('third', date('now')),
    ('fourth', date('now')),
    ('fifth', date('now'));

  INSERT INTO queue_members (user_id, user_first_name, user_last_name, user_username, queue_id, crossed, position)
  VALUES
    (1, 'Anton', 'Bodiak', 'levant47', 1, 1, 0),
    (2, 'Sanya', 'Sanya', 'Sanya', 1, 1, 2),
    (3, 'Danya', 'Danya', 'Danya', 1, 1, 1),
    (4, 'Anthony', 'Anthony', 'Anthony', 1, 0, 3),
    (5, 'Sanya', 'Zlobin', 'Zhaba', 2, 0, 0),
    (6, 'Anton', 'Bodiak', 'levant47', 3, 0, 0);
" | sqlite3 ../nureq.db

