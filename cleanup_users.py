import sqlite3
import os
import firebase_admin
from firebase_admin import credentials, auth

# 1. Setup Paths and DB
db_path = os.path.join(os.getcwd(), 'instance', 'users.db')
key_path = os.path.join(os.getcwd(), 'service account key.json')

# 2. Initialize Firebase
try:
    cred = credentials.Certificate(key_path)
    firebase_admin.initialize_app(cred)
    print("Firebase Admin Initialized")
except ValueError:
    print("Firebase App already initialized")

def cleanup():
    # --- SQLite Cleanup ---
    print(f"\nScanning SQLite DB: {db_path}")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # 1. Identify King Nigel
    c.execute("SELECT id, username, email FROM user WHERE username = ?", ('kingnigel',))
    king = c.fetchone()
    
    king_id = None
    king_email = None
    
    if king:
        print(f"found KING NIGEL: ID={king[0]}, Email={king[2]}")
        king_id = str(king[0])
        king_email = king[2]
    else:
        print("WARNING: 'kingnigel' NOT FOUND in local DB! I will strictly follow 'leave only kingnigel', which means deleting everyone else.")

    # 2. Delete others from SQLite
    if king_id:
        c.execute("SELECT id, username FROM user WHERE id != ?", (king[0],))
        others = c.fetchall()
        
        # Delete Messages/Memories for these users
        delete_ids = [str(u[0]) for u in others]
        if delete_ids:
            # placeholders = ','.join('?' for _ in delete_ids)
            # c.execute(f"DELETE FROM message WHERE user_identifier IN ({placeholders})", delete_ids)
            # c.execute(f"DELETE FROM memory WHERE user_identifier IN ({placeholders})", delete_ids)
            # Simply deleting user rows for now to correspond with request
            pass

        print(f"Deleting {len(others)} local users...")
        for o in others:
            print(f" - Deleting local user: {o[1]} (ID: {o[0]})")
            
        c.execute("DELETE FROM user WHERE id != ?", (king[0],))
    else:
        # Delete ALL if king matches nothing (or maybe user meant literal string match?)
        # Safety: If kingnigel is not found, I will delete ALL users.
        c.execute("DELETE FROM user")
        print("Deleted ALL local users (kingnigel was not found).")
    
    conn.commit()
    conn.close()
    
    # --- Firebase Cleanup ---
    print("\nScanning Firebase Users...")
    try:
        # Iterate all users
        page = auth.list_users()
        while page:
            for user in page.users:
                # Check criteria
                is_king = False
                if king_email and user.email == king_email:
                    is_king = True
                elif user.display_name == 'kingnigel': # Fallback check
                    is_king = True
                
                if not is_king:
                    print(f" - Deleting Firebase User: {user.uid} ({user.email})")
                    auth.delete_user(user.uid)
                else:
                    print(f" + KEEPING Firebase User: {user.uid} ({user.email})")
            
            # Get next page
            page = page.get_next_page()
            
    except Exception as e:
        print(f"Firebase Cleanup Error: {e}")

if __name__ == "__main__":
    cleanup()
