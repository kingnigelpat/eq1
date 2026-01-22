import sys
import os

print(f"Python executable: {sys.executable}")

print("Attempting to import sqlite3...")
try:
    import sqlite3
    print(f"sqlite3 version: {sqlite3.sqlite_version}")
except ImportError as e:
    print(f"Failed to import sqlite3: {e}")

print("Attempting to import sqlalchemy...")
try:
    import sqlalchemy
    from sqlalchemy import create_engine
    print(f"SQLAlchemy version: {sqlalchemy.__version__}")
    
    print("Attempting to create engine...")
    engine = create_engine('sqlite:///test_debug.db')
    print("Engine created.")
    
    print("Attempting to connect...")
    with engine.connect() as conn:
        print("Connection successful.")
except Exception as e:
    print(f"SQLAlchemy error: {e}")
    import traceback
    traceback.print_exc()
