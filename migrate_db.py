import sqlite3
import os

db_path = os.path.join(os.getcwd(), 'instance', 'users.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if column exists
cursor.execute("PRAGMA table_info(user)")
cols = [col[1] for col in cursor.fetchall()]

if 'email' not in cols:
    print("Adding email column to user table...")
    try:
        cursor.execute("ALTER TABLE user ADD COLUMN email VARCHAR(150)")
        conn.commit()
        print("Success.")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("Email column already exists.")

conn.close()
