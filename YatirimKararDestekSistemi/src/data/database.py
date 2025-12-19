#(Bağlantı ayarları)
# # src/data/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

# Proje kök dizinini bulup .env yüklüyoruz
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, ".env"))

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

# MySQL bağlantı stringi
DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"

# Echo=False yaptık, gereksiz log kalabalığı olmasın
engine = create_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency Injection için DB oturumu sağlar"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Tabloları oluşturur"""
    from src.data import models  # Modelleri içeri aktar ki Base haberdar olsun
    Base.metadata.create_all(bind=engine)