import sqlite3
import os

db_path = r"c:\Users\gabri\Desktop\sites\campeaodochurrasco1\campeao.db"

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Adding sub_category column to products table...")
        cursor.execute("ALTER TABLE products ADD COLUMN sub_category TEXT")
        conn.commit()
        print("Migration successful!")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Column sub_category already exists.")
        else:
            print(f"Operational error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
else:
    print(f"Database {db_path} not found.")
