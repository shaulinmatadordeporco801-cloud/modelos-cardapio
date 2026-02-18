import os
from database import SessionLocal
from models import Product
from difflib import get_close_matches

def link_images():
    db = SessionLocal()
    products = db.query(Product).all()
    
    image_dir = "images"
    if not os.path.exists(image_dir):
        print("Pasta 'images' não encontrada.")
        return

    image_files = os.listdir(image_dir)
    print(f"Arquivos encontrados: {image_files}")

    updated_count = 0
    
    # Map product names to IDs for easier lookup
    product_names = [p.name for p in products]

    for filename in image_files:
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.avif')):
            continue

        # Try to find a match
        name_part = os.path.splitext(filename)[0]
        match = get_close_matches(name_part.lower(), [n.lower() for n in product_names], n=1, cutoff=0.4)
        
        if match:
            matched_name = match[0]
            # Find the actual product with this name (case insensitive match needed technically, but let's loop)
            target_product = next((p for p in products if p.name.lower() == matched_name), None)
            
            if target_product:
                image_url = f"/static/images/{filename}"
                print(f"Vinculando '{filename}' -> Produto: '{target_product.name}'")
                target_product.image_url = image_url
                updated_count += 1
        else:
            print(f"Sem correspondência para: {filename}")

    db.commit()
    print(f"Total de produtos atualizados: {updated_count}")
    db.close()

if __name__ == "__main__":
    link_images()
