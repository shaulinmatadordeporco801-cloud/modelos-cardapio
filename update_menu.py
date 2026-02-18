from database import SessionLocal
from models import Category, Product

def update_menu():
    db = SessionLocal()
    
    # Get Category
    cat_espetinhos = db.query(Category).filter_by(name="Espetinhos").first()
    if not cat_espetinhos:
        print("Categoria 'Espetinhos' não encontrada!")
        return

    # Items to add (Name, Description, Price)
    # Using data from constants.tsx where matches, and estimates for others
    new_items = [
        ("Fraldinha", "Fraldinha suculenta assada na brasa", 12.00),
        ("Medalhão", "Frango macio envolvido com bacon crocante", 9.00),
        ("Tulipa", "Crocante por fora, suculenta por dentro", 9.00),
        ("Frango", "Leve, macio e bem temperado", 9.00),
        ("Coração", "Temperado na medida certa e assado no ponto ideal", 8.00),
        ("Linguiça", "Linguiça toscana suculenta e douradinha", 9.00),
        ("Panceta", "Carne com pele pururuca e crocante", 9.00),
        ("Queijo", "Queijo coalho dourado por fora, derretendo por dentro", 7.00),
        ("Pão de alho", "Crocante, macio e com sabor marcante de alho", 8.00),
        ("Kafta", "Carne bovina bem temperada e suculenta", 9.00),
        ("Kafta de Frango", "Kafta de frango leve e saborosa", 9.00),
        ("Romeu e Julieta", "Combinação perfeita de queijo com goiabada", 10.00),
    ]

    print("Adicionando itens...")
    
    for name, desc, price in new_items:
        # Check if exists to avoid duplicates (optional, but good practice)
        existing = db.query(Product).filter_by(name=name, category_id=cat_espetinhos.id).first()
        if existing:
            print(f"Atualizando {name}...")
            existing.description = desc
            existing.price = price
        else:
            print(f"Criando {name}...")
            new_prod = Product(name=name, description=desc, price=price, category=cat_espetinhos)
            db.add(new_prod)
    
    db.commit()
    print("Concluído! Itens adicionados/atualizados.")
    db.close()

if __name__ == "__main__":
    update_menu()
