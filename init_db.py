from database import engine, Base, SessionLocal
from models import Category, Product
import os

# Create global tables
Base.metadata.create_all(bind=engine)

def init_db():
    db = SessionLocal()
    
    # Check if data already exists
    if db.query(Category).first():
        print("Banco de dados já contem dados.")
        return

    # Create Categories
    cat_espetinhos = Category(name="Espetinhos")
    cat_bebidas = Category(name="Bebidas")
    cat_guim = Category(name="Acompanhamentos")

    db.add_all([cat_espetinhos, cat_bebidas, cat_guim])
    db.commit()

    # Create Initial Products
    products = [
        Product(name="Espetinho de Picanha", description="Saborosa picanha no espeto", price=12.00, category=cat_espetinhos),
        Product(name="Espetinho de Frango", description="Peito de frango suculento", price=8.00, category=cat_espetinhos),
        Product(name="Espetinho de Linguiça", description="Linguiça toscana especial", price=7.00, category=cat_espetinhos),
        Product(name="Coca-Cola Lata", description="Lata 350ml", price=5.00, category=cat_bebidas),
        Product(name="Arroz Branco", description="Porção individual", price=6.00, category=cat_guim),
    ]

    db.add_all(products)
    db.commit()
    print("Banco de dados inicializado com sucesso!")

if __name__ == "__main__":
    init_db()
