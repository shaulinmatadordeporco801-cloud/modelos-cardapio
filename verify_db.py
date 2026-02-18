import sys
sys.path.append('.')
from database import SessionLocal
from models import Category, Product

def verify():
    db = SessionLocal()
    
    print("--- Categorias ---")
    categories = db.query(Category).all()
    for cat in categories:
        print(f"ID: {cat.id} | Nome: {cat.name}")

    print("\n--- Produtos ---")
    products = db.query(Product).all()
    for prod in products:
        print(f"ID: {prod.id} | Nome: {prod.name} | Preço: R${prod.price:.2f} | Categoria: {prod.category.name}")
    
    db.close()

if __name__ == "__main__":
    verify()
