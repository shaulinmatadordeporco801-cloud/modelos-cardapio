from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    
    products = relationship("Product", back_populates="category")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    price = Column(Float)
    category_id = Column(Integer, ForeignKey("categories.id"))
    image_url = Column(String, nullable=True)
    is_available = Column(Boolean, default=True)
    sub_category = Column(String, nullable=True, index=True) # e.g., 'Cervejas', 'Refrigerantes', 'Águas'

    category = relationship("Category", back_populates="products")

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String)
    customer_phone = Column(String)
    total_amount = Column(Float)
    status = Column(String, default="Pendente") # Pendente, Preparando, Pronto, Entregue
    created_at = Column(DateTime, default=datetime.utcnow)
