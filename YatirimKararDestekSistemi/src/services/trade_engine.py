from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from src.data.models import PortfolioHolding, Transaction, Security, User

class TradeService:
    def __init__(self, db: Session):
        self.db = db

    # custom_date parametresi eklendi (Opsiyonel)
    def execute_buy(self, user_id: int, symbol: str, quantity: float, price: float, custom_date: datetime = None):
        try:
            trade_date = custom_date if custom_date else datetime.now()
            
            security = self._get_or_create_security(symbol)
            
            # Transaction Kaydı
            new_txn = Transaction(
                user_id=user_id,
                security_id=security.id,
                side="BUY",
                quantity=quantity,
                price=price,
                trade_date=trade_date  # Seçilen tarih
            )
            self.db.add(new_txn)

            # Holding Güncelleme
            holding = self.db.query(PortfolioHolding).filter(
                and_(PortfolioHolding.user_id == user_id, PortfolioHolding.security_id == security.id)
            ).first()

            if not holding:
                holding = PortfolioHolding(
                    user_id=user_id,
                    security_id=security.id,
                    quantity=quantity,
                    avg_cost=price
                )
                self.db.add(holding)
            else:
                old_cost_total = float(holding.quantity) * float(holding.avg_cost)
                new_cost_total = float(quantity) * float(price)
                total_qty = float(holding.quantity) + float(quantity)
                
                new_avg_cost = (old_cost_total + new_cost_total) / total_qty
                
                holding.quantity = total_qty
                holding.avg_cost = new_avg_cost

            self.db.commit()
            return {"status": "success", "message": f"{symbol} portföye eklendi."}

        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": str(e)}

    # custom_date parametresi eklendi
    def execute_sell(self, user_id: int, symbol: str, quantity: float, price: float, custom_date: datetime = None):
        try:
            trade_date = custom_date if custom_date else datetime.now()

            security = self.db.query(Security).filter(Security.symbol == symbol).first()
            if not security:
                raise ValueError("Hisse bulunamadı.")

            holding = self.db.query(PortfolioHolding).filter(
                and_(PortfolioHolding.user_id == user_id, PortfolioHolding.security_id == security.id)
            ).first()

            if not holding or float(holding.quantity) < quantity:
                raise ValueError(f"Yetersiz bakiye! Mevcut: {holding.quantity if holding else 0}")

            new_txn = Transaction(
                user_id=user_id,
                security_id=security.id,
                side="SELL",
                quantity=quantity,
                price=price,
                trade_date=trade_date # Seçilen tarih
            )
            self.db.add(new_txn)

            holding.quantity = float(holding.quantity) - quantity
            
            if holding.quantity <= 0:
                self.db.delete(holding)

            self.db.commit()
            return {"status": "success", "message": f"{symbol} satıldı."}

        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": str(e)}

    def _get_or_create_security(self, symbol: str):
        sec = self.db.query(Security).filter(Security.symbol == symbol).first()
        if not sec:
            sec = Security(symbol=symbol, name=symbol)
            self.db.add(sec)
            self.db.commit()
        return sec