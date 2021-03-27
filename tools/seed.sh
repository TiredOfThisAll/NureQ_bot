echo "
  PRAGMA foreign_keys = ON;

  DELETE
  FROM queues;

  INSERT INTO queues (name, last_updated_on)
  VALUES
    ('first', date('now')),
    ('second', date('now')),
    ('third', date('now')),
    ('fourth', date('now')),
    ('fifth', date('now'));

  INSERT INTO queue_members (user_id, user_first_name, user_last_name, user_username, queue_id, crossed)
  VALUES
    (1, 'Anton', 'Bodiak', 'levant47', 1, 0),
    (2, 'Sanya', 'Zlobin', 'Zhaba', 2, 1),
    (3, 'Anton', 'Bodiak', 'levant47', 3, 1);
" | sqlite3 ../nureq.db

