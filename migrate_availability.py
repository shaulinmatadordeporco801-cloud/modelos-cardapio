import sqlite3
import os

db_path = r"c:\Users\gabri\Desktop\sites\campeaodochurrasco1\campeao.db"

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(products)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if "is_available" not in columns:
            print("Adding 'is_available' column to 'products' table...")
            cursor.execute("ALTER TABLE products ADD COLUMN is_available BOOLEAN DEFAULT 1")
            conn.commit()
            print("Migration successful!")
        else:
            print("Column 'is_available' already exists.")
            
    except Exception as e:
        print(f"Error during migration: {e}")
    finally:
        conn.close()
else:
    print(f"Database {db_path} not found.")
