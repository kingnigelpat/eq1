import sqlite3

def list_tables():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    print(c.fetchall())
    conn.close()

if __name__ == "__main__":
    list_tables()
