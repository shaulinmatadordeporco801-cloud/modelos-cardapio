from database import SessionLocal
from models import Product

def remove_items():
    db = SessionLocal()
    items_to_remove = ["Espetinho de Picanha", "Espetinho de Frango", "Espetinho de Linguiça"]
    
    print("Removendo itens...")
    for name in items_to_remove:
        product = db.query(Product).filter_by(name=name).first()
        if product:
            print(f"Removendo: {product.name} (ID: {product.id})")
            db.delete(product)
        else:
            print(f"Item não encontrado: {name}")
    
    db.commit()
    print("Concluído.")
    db.close()

if __name__ == "__main__":
    remove_items()
