from database import SessionLocal
from models import Product, Category

db = SessionLocal()
products = db.query(Product).all()
print("Produtos atuais:")
for p in products:
    print(f"- {p.name} (ID: {p.id}, Categoria: {p.category.name})")
db.close()
