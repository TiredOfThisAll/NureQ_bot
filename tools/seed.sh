echo "
  PRAGMA foreign_keys = ON;

  DELETE FROM queues;
  DELETE FROM admins;
  DELETE FROM logs;

  INSERT INTO queues (name, last_updated_on)
  VALUES
    ('first', date('now')),
    ('second', date('now')),
    ('third', date('now')),
    ('fourth', date('now')),
    ('fifth', date('now'));

  INSERT INTO queue_members
    (user_id, user_first_name, user_last_name, user_username, queue_id, crossed, position)
  VALUES
    (1,       'Anton',         'Bodiak',       'levant47',    1,        1,       0),
    (2,       'Sanya',         'Sanya',        'Sanya',       1,        1,       1),
    (3,       'Danya',         'Danya',        'Danya',       1,        1,       2),
    (4,       'Anthony',       'Anthony',      'Anthony',     1,        1,       3),
    (5,       'Sergio',        'Gavrilov',     'Serg',        1,        1,       4),
    (6,       'Boris',         'Borisov',      'Bor',         1,        1,       5),
    (7,       'Dima',          'Dimovi4',      'Dim',         1,        0,       6),
    (8,       'Sanya',         'Zlobin',       'Zhaba',       2,        0,       0),
    (9,       'Anton',         'Bodiak',       'levant47',    3,        0,       0);

  INSERT INTO admins (user_id)
  VALUES
    (477243002),
    (668426468);

  INSERT INTO logs (level, timestamp, message)
  VALUES
    ('INFO', date('now'), 'Info log'),
    ('WARN', date('now'), 'Warn log'),
    ('ERROR', date('now'), 'Error log');
" | sqlite3 ../nureq.db

