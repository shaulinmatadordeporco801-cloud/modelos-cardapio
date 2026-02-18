import sqlite3
import os

db_path = r"c:\Users\gabri\Desktop\sites\campeaodochurrasco1\campeao.db"

beverages = [
    # Cervejas
    ("Cerveja Heineken Gelada 330ml", "Long Neck Heineken", 10.00, "Cervejas"),
    ("Cerveja Puro Malte Império 350ml", "Lata Império", 6.00, "Cervejas"),
    ("Cerveja Nacional Brahma 350ml", "Lata Brahma", 6.00, "Cervejas"),
    ("Cerveja Skol 350ml", "Lata Skol", 6.00, "Cervejas"),
    
    # Refrigerantes
    ("Refrigerante Coca Cola Lata Zero", "Lata 350ml", 6.00, "Refrigerantes"),
    ("Coca-Cola Original 350ml", "Lata 350ml", 6.00, "Refrigerantes"),
    ("Refrigerante Guaraná Antarctica 350ml", "Lata 350ml", 6.00, "Refrigerantes"),
    ("Refrigerante Zero Pepsi 350ml", "Lata 350ml", 6.00, "Refrigerantes"),
    ("Coca Cola 2L", "Garrafa PET", 14.00, "Refrigerantes"),
    ("Refrigerante Guaraná Antártica 1L", "Garrafa PET", 10.00, "Refrigerantes"),
    ("Refrigerante H2oh 500ml Limão", "Garrafa PET", 8.00, "Refrigerantes"),
    ("Refrigerante H2O Limoneto Pet 500ml", "Garrafa PET", 8.00, "Refrigerantes"),
    
    # Águas
    ("Água Sem Gás 500 Ml", "Garrafa 500ml", 4.00, "Águas"),
    ("Água Com Gás 500 Ml", "Garrafa 500ml", 4.00, "Águas"),
    ("Água Tônica Zero Antárctica 350ml", "Lata 350ml", 6.00, "Águas"),
    
    # Outros / Sucos
    ("Suco de Acerola", "Copo", 8.00, "Outros"),
    ("Suco da Fruta", "Copo", 8.00, "Outros")
]

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Inserting new beverages...")
        category_id = 2 # Bebidas
        
        for name, desc, price, sub_cat in beverages:
            cursor.execute("""
                INSERT INTO products (name, description, price, category_id, is_available, sub_category)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, desc, price, category_id, True, sub_cat))
            
        conn.commit()
        print("Bebidas inseridas com sucesso!")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
else:
    print(f"Database {db_path} not found.")
