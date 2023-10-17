import sqlite3

conn = sqlite3.connect('database.db')

c = conn.cursor()

# Create table for users
conn.execute('CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL, password TEXT NOT NULL, role TEXT NOT NULL, company TEXT);')


c.execute('''CREATE TABLE posts (
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  user_id INTEGER NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users (id)
);''')


c.execute('''CREATE TABLE scores (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  criteria TEXT NOT NULL,
  score INTEGER NOT NULL,
  evaluator_id INTEGER NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users (id),
  FOREIGN KEY (evaluator_id) REFERENCES users (id)
);''')

# Commit changes
conn.commit()

# Close connection
conn.close()
