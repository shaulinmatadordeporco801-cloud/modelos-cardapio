from database import SessionLocal
from models import Product, Category

def update_data():
    db = SessionLocal()
    
    # 1. Fix Fraldinha Image
    fraldinha = db.query(Product).filter(Product.name.ilike("%Fraldinha%")).first()
    if fraldinha:
        print(f"Atualizando imagem da Fraldinha (antes: {fraldinha.image_url})")
        fraldinha.image_url = "/static/images/carne.avif"
    else:
        print("Fraldinha não encontrada!")

    # 2. Update Prices for Espetinhos
    cat_espetinhos = db.query(Category).filter_by(name="Espetinhos").first()
    if cat_espetinhos:
        products = db.query(Product).filter_by(category_id=cat_espetinhos.id).all()
        
        for p in products:
            name_lower = p.name.lower()
            old_price = p.price
            
            if "queijo" in name_lower:
                new_price = 7.00
            elif "coração" in name_lower or "pão de alho" in name_lower:
                new_price = 8.00
            else:
                new_price = 9.00
            
            if old_price != new_price:
                p.price = new_price
                print(f"Atualizando preço: {p.name} | R$ {old_price} -> R$ {new_price}")
    
    db.commit()
    print("Atualizações concluídas!")
    db.close()

if __name__ == "__main__":
    update_data()
