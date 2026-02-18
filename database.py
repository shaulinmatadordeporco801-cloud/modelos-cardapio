import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database URL from environment or fallback to SQLite
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./campeao.db")

# Fix for Heroku/Render PostgreSQL URLs (replace postgres:// with postgresql://)
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # Auto-adjust port for Supabase Pooler if using the pooler address but wrong port
    if ".pooler.supabase.com" in SQLALCHEMY_DATABASE_URL and ":5432" in SQLALCHEMY_DATABASE_URL:
        SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace(":5432", ":6543")
        print("🔧 Auto-corrigindo porta do Pooler da Supabase para 6543")
    
    # Increase pool size and handle disconnected connections
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=300
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
