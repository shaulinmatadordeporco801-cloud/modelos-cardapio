import sqlite3
import os

db_path = r"c:\Users\gabri\Desktop\sites\campeaodochurrasco1\campeao.db"

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Update Guaraná Antarctica 350ml
        cursor.execute("UPDATE products SET image_url = ? WHERE name LIKE ?", 
                       ("/static/images/Refrigerante Guaraná Antarctica 350ml.webp", "%Guaraná Antarctica 350ml%"))
        
        # Update Coca-Cola Original 350ml
        cursor.execute("UPDATE products SET image_url = ? WHERE name LIKE ?", 
                       ("/static/images/Coca-Cola Original 350ml.webp", "%Coca-Cola Original 350ml%"))
        
        conn.commit()
        print(f"Updates successful! Rows affected: {cursor.rowcount}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
else:
    print(f"Database {db_path} not found.")
