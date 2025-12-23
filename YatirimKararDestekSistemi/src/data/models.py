from sqlalchemy import Column, String, Date, DateTime, ForeignKey, Enum, DECIMAL, Text, Float, Integer
from sqlalchemy.dialects.mysql import INTEGER, BIGINT
from sqlalchemy.orm import relationship
from datetime import datetime
from src.data.database import Base

# --- 1. KULLANICILAR ---
class User(Base):
    __tablename__ = 'users'
    
    id = Column(INTEGER(unsigned=True), primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True)
    password_hash = Column(String(255))
    risk_profile = Column(Enum('temkinli', 'orta', 'agresif'), default='orta')
    created_at = Column(DateTime, default=datetime.now)

    # İlişkiler
    holdings = relationship("PortfolioHolding", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")
    sim_sessions = relationship("SimSession", back_populates="user")
    
    # --- YENİ EKLENEN İLİŞKİLER (Bu satırlar eksikti) ---
    budgets = relationship("Budget", back_populates="user")
    goals = relationship("FinancialGoal", back_populates="user")
    # ----------------------------------------------------
    risk_score = Column(Integer, default=0)
    risk_label = Column(String(20), default="Bilinmiyor") # "AGRESİF" gibi kısa metinler için 20 yeter

# --- 2. HİSSE SENETLERİ ---
class Security(Base):
    __tablename__ = 'securities'
    
    id = Column(INTEGER(unsigned=True), primary_key=True)
    symbol = Column(String(20), unique=True, nullable=False)
    name = Column(String(100))
    exchange = Column(String(20), default='BIST')
    currency = Column(String(10), default='TRY')
    created_at = Column(DateTime, default=datetime.now)

    # İlişkiler
    prices = relationship("PriceHistory", back_populates="security")
    predictions = relationship("AiPrediction", back_populates="security")

# --- 3. FİYAT GEÇMİŞİ ---
class PriceHistory(Base):
    __tablename__ = 'price_history'
    
    id = Column(BIGINT(unsigned=True), primary_key=True)
    security_id = Column(INTEGER(unsigned=True), ForeignKey('securities.id'), nullable=False)
    date = Column(Date, nullable=False)
    open_price = Column(DECIMAL(10, 4))
    high_price = Column(DECIMAL(10, 4))
    low_price = Column(DECIMAL(10, 4))
    close_price = Column(DECIMAL(10, 4), nullable=False)
    volume = Column(BIGINT)

    security = relationship("Security", back_populates="prices")

# --- 4. GERÇEK İŞLEMLER (LOG KAYDI) ---
class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(BIGINT(unsigned=True), primary_key=True)
    user_id = Column(INTEGER(unsigned=True), ForeignKey('users.id'), nullable=False)
    security_id = Column(INTEGER(unsigned=True), ForeignKey('securities.id'), nullable=False)
    
    trade_date = Column(DateTime, default=datetime.now, nullable=False)
    side = Column(Enum('BUY', 'SELL'), nullable=False)
    quantity = Column(DECIMAL(18, 4), nullable=False)
    price = Column(DECIMAL(18, 4), nullable=False)
    fee = Column(DECIMAL(18, 4), default=0)
    note = Column(String(255))

    user = relationship("User", back_populates="transactions")
    security = relationship("Security")

# --- 5. PORTFÖY (ANLIK DURUM) ---
class PortfolioHolding(Base):
    __tablename__ = 'portfolio_holdings'
    
    user_id = Column(INTEGER(unsigned=True), ForeignKey('users.id'), primary_key=True)
    security_id = Column(INTEGER(unsigned=True), ForeignKey('securities.id'), primary_key=True)
    
    quantity = Column(DECIMAL(18, 4), default=0)
    avg_cost = Column(DECIMAL(18, 4), default=0)
    current_value = Column(DECIMAL(18, 4))

    user = relationship("User", back_populates="holdings")
    security = relationship("Security")

# --- 6. AI TAHMİNLERİ ---
class AiPrediction(Base):
    __tablename__ = 'ai_predictions'
    
    id = Column(BIGINT(unsigned=True), primary_key=True)
    security_id = Column(INTEGER(unsigned=True), ForeignKey('securities.id'), nullable=False)
    
    prediction_date = Column(Date, default=datetime.utcnow)
    target_date = Column(Date, nullable=False)
    predicted_price = Column(DECIMAL(18, 4))
    model_name = Column(String(50))
    confidence_score = Column(DECIMAL(5, 2))
    signal = Column(String(20))

    security = relationship("Security", back_populates="predictions")

# --- 7. SİMÜLASYON ---
class SimSession(Base):
    __tablename__ = 'sim_sessions'
    id = Column(BIGINT(unsigned=True), primary_key=True)
    user_id = Column(INTEGER(unsigned=True), ForeignKey('users.id'))
    name = Column(String(100))
    initial_capital = Column(DECIMAL(18, 4))
    status = Column(Enum('ACTIVE', 'FINISHED'), default='ACTIVE')
    
    user = relationship("User", back_populates="sim_sessions")

# --- 8. DUYGU ANALİZİ ---
class SentimentLog(Base):
    __tablename__ = 'sentiment_logs'
    id = Column(BIGINT(unsigned=True), primary_key=True)
    security_id = Column(INTEGER(unsigned=True), ForeignKey('securities.id'))
    source = Column(String(50))
    sentiment_score = Column(DECIMAL(5, 2))
    content_summary = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

# --- 9. PLANLAMA VE BÜTÇE (YENİ) ---

class Budget(Base):
    __tablename__ = 'budgets'
    id = Column(Integer, primary_key=True, index=True)
    
    # unsigned=True düzeltmesi yapıldı
    user_id = Column(INTEGER(unsigned=True), ForeignKey('users.id'), nullable=False)
    
    month = Column(String(7), nullable=False) # Örn: "2025-01"
    
    income_salary = Column(Float, default=0.0)
    income_additional = Column(Float, default=0.0)
    
    expense_rent = Column(Float, default=0.0)
    expense_bills = Column(Float, default=0.0)
    expense_food = Column(Float, default=0.0)
    expense_transport = Column(Float, default=0.0)
    expense_luxury = Column(Float, default=0.0)
    
    savings_target = Column(Float, default=0.0)

    user = relationship("User", back_populates="budgets")

class FinancialGoal(Base):
    __tablename__ = 'financial_goals'
    id = Column(Integer, primary_key=True, index=True)
    
    # unsigned=True düzeltmesi yapıldı
    user_id = Column(INTEGER(unsigned=True), ForeignKey('users.id'), nullable=False)
    
    name = Column(String(100), nullable=False)
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, default=0.0)
    deadline = Column(Date, nullable=False)
    priority = Column(String(10), default="MEDIUM")
    status = Column(String(10), default="ACTIVE")
    
    user = relationship("User", back_populates="goals")