
import sqlite3
import re

def inspect_db():
    conn = sqlite3.connect('campeao.db')
    cursor = conn.cursor()
    
    tables = ['products', 'categories']
    
    for table in tables:
        print(f"\n--- Inspecionando tabela: {table} ---")
        cursor.execute(f"SELECT * FROM {table}")
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        
        for row in rows:
            for i, val in enumerate(row):
                if isinstance(val, str):
                    # Check for phone numbers
                    if re.search(r'\(?[0-9]{2}\)?\s?[0-9]{4,5}-?[0-9]{4}', val):
                        print(f"TELEFONE encontrado em {table}.{columns[i]} (ID {row[0]}): {val}")
                    # Check for links (http/https)
                    if 'http' in val.lower() or 'www.' in val.lower():
                        # Exclude image URLs as they are needed for display unless requested otherwise
                        if not any(ext in val.lower() for ext in ['.jpg', '.png', '.webp', '.jpeg']):
                            print(f"LINK encontrado em {table}.{columns[i]} (ID {row[0]}): {val}")
    
    conn.close()

if __name__ == "__main__":
    inspect_db()
