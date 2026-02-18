import sqlite3

def list_users():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute("SELECT id, username, email FROM user")
        users = c.fetchall()
        print(f"Found {len(users)} users:")
        for u in users:
            print(f"ID: {u[0]}, Username: {u[1]}, Email: {u[2]}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    list_users()
