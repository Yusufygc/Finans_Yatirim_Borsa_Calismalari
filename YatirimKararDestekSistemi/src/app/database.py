from sqlalchemy import create_engine, Column, String, Float, Date, ForeignKey, Enum, DECIMAL
# DÜZELTME: MySQL'e özgü INTEGER tipini çağırıyoruz (UNSIGNED desteği için)
from sqlalchemy.dialects.mysql import INTEGER 
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from datetime import datetime
import os
from dotenv import load_dotenv

# .env dosyasını yükle
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Ortam değişkenlerinden verileri al
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

# Veritabanı bağlantı URL'si
DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"

Base = declarative_base()
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- MODELLER ---

class User(Base):
    __tablename__ = 'users'
    # SQL'deki 'INT UNSIGNED' ile eşleşmesi için unsigned=True yapıyoruz
    id = Column(INTEGER(unsigned=True), primary_key=True, index=True) 
    username = Column(String(50), unique=True)
    email = Column(String(100), unique=True)
    risk_profile = Column(Enum('temkinli', 'orta', 'agresif'), default='orta')
    
    portfolio_holdings = relationship("PortfolioHolding", back_populates="user")

class Security(Base):
    __tablename__ = 'securities'
    # SQL'deki 'INT UNSIGNED' ile eşleşmesi için unsigned=True
    id = Column(INTEGER(unsigned=True), primary_key=True)
    symbol = Column(String(20), unique=True)
    name = Column(String(100))
    
    prices = relationship("PriceHistory", back_populates="security")
    predictions = relationship("AiPrediction", back_populates="security")

class PriceHistory(Base):
    __tablename__ = 'price_history'
    # SQL'de id BIGINT UNSIGNED olabilir, ama Python tarafında Integer genelde yeterlidir. 
    # Yine de foreign key uyumu şart.
    id = Column(INTEGER(unsigned=True), primary_key=True)
    security_id = Column(INTEGER(unsigned=True), ForeignKey('securities.id')) # DÜZELTME
    date = Column(Date)
    close_price = Column(DECIMAL(10, 4))
    
    security = relationship("Security", back_populates="prices")

class PortfolioHolding(Base):
    __tablename__ = 'portfolio_holdings' 
    # Foreign Key'ler unsigned olmalı çünkü referans verdikleri tablolar unsigned
    user_id = Column(INTEGER(unsigned=True), ForeignKey('users.id'), primary_key=True) # DÜZELTME
    security_id = Column(INTEGER(unsigned=True), ForeignKey('securities.id'), primary_key=True) # DÜZELTME
    quantity = Column(DECIMAL(18, 4), default=0)
    avg_cost = Column(DECIMAL(18, 4), default=0)
    
    user = relationship("User", back_populates="portfolio_holdings")
    security = relationship("Security")

class AiPrediction(Base):
    __tablename__ = 'ai_predictions'
    id = Column(INTEGER(unsigned=True), primary_key=True) # ID'leri de unsigned yapalım
    # DÜZELTME: security_id artık UNSIGNED INT, securities.id ile uyumlu
    security_id = Column(INTEGER(unsigned=True), ForeignKey('securities.id')) 
    prediction_date = Column(Date, default=datetime.utcnow)
    target_date = Column(Date)
    predicted_price = Column(DECIMAL(18, 4))
    signal = Column(String(20)) 
    confidence = Column(Float)
    
    security = relationship("Security", back_populates="predictions")

def init_db():
    Base.metadata.create_all(bind=engine)