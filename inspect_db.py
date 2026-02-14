import sqlite3
import os

db_path = os.path.join('instance', 'users.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables:", tables)

# Check columns for 'user' table if it exists
for table in tables:
    table_name = table[0]
    print(f"\nColumns in {table_name}:")
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    for col in columns:
        print(col)

conn.close()
