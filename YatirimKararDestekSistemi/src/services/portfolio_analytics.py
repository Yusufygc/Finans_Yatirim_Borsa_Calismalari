from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from datetime import datetime, timedelta
import pandas as pd
from src.data.models import PortfolioHolding, Transaction, PriceHistory, Security

class PortfolioAnalyticsService:
    """
    Profesyonel Aracı Kurum Seviyesinde Portföy Analitiği.
    Dönemsel getiriler, lot bazlı maliyet analizleri ve ağırlık hesaplamaları içerir.
    """
    def __init__(self, db: Session):
        self.db = db

    def generate_dashboard(self, user_id: int):
        """
        Tüm analizleri tek bir çatı altında toplayan ana fonksiyon.
        """
        # 1. Temel Veriler
        holdings = self._get_active_holdings(user_id)
        if not holdings:
            return {"error": "Portföy boş."}

        # 2. Analiz Modülleri
        period_returns = self._calculate_period_returns(holdings)
        lot_analysis = self._analyze_lots(user_id, holdings)
        weights = self._calculate_weights(holdings)
        stats = self._calculate_extremes(holdings)

        return {
            "summary": period_returns["portfolio_summary"], # Genel Portföy Getirileri
            "details": period_returns["asset_details"],     # Hisse Bazlı Dönemsel Getiriler
            "lot_breakdown": lot_analysis,                  # Parçalı Alım Analizi
            "allocation": weights,                          # Portföy Ağırlıkları
            "performance_stats": stats                      # En İyi/En Kötü
        }

    def _get_active_holdings(self, user_id):
        """Aktif portföyü ve güncel fiyatları çeker."""
        holdings = self.db.query(PortfolioHolding).filter(PortfolioHolding.user_id == user_id).all()
        data = []
        for h in holdings:
            # En güncel fiyatı al
            last_price_row = self.db.query(PriceHistory).filter(
                PriceHistory.security_id == h.security_id
            ).order_by(PriceHistory.date.desc()).first()
            
            current_price = float(last_price_row.close_price) if last_price_row else float(h.avg_cost)
            
            data.append({
                "security_id": h.security_id,
                "symbol": h.security.symbol,
                "quantity": float(h.quantity),
                "avg_cost": float(h.avg_cost),
                "current_price": current_price,
                "market_value": float(h.quantity) * current_price
            })
        return data

    def _get_historical_price(self, security_id, days_ago):
        """Belirtilen gün kadar önceki kapanış fiyatını (veya en yakın tarihi) bulur."""
        target_date = datetime.now().date() - timedelta(days=days_ago)
        
        # Tam o gün yoksa, o günden önceki en yakın tarihi al (Pazar ise Cuma)
        price_row = self.db.query(PriceHistory).filter(
            and_(
                PriceHistory.security_id == security_id,
                PriceHistory.date <= target_date
            )
        ).order_by(PriceHistory.date.desc()).first()
        
        return float(price_row.close_price) if price_row else None

    def _calculate_period_returns(self, holdings):
        """Günlük, Haftalık, Aylık, Yıllık değişim oranları."""
        asset_details = []
        total_value_now = sum(h["market_value"] for h in holdings)
        
        # Ağırlıklı getiri hesaplamak için değişkenler
        weighted_daily_sum = 0
        weighted_weekly_sum = 0
        weighted_monthly_sum = 0
        
        for h in holdings:
            p_now = h["current_price"]
            
            # Geçmiş fiyatlar
            p_day = self._get_historical_price(h["security_id"], 1) or p_now
            p_week = self._get_historical_price(h["security_id"], 7) or p_now
            p_month = self._get_historical_price(h["security_id"], 30) or p_now
            p_year = self._get_historical_price(h["security_id"], 365) or p_now
            
            # Yüzdesel Değişimler
            d_chg = ((p_now - p_day) / p_day) * 100
            w_chg = ((p_now - p_week) / p_week) * 100
            m_chg = ((p_now - p_month) / p_month) * 100
            y_chg = ((p_now - p_year) / p_year) * 100
            
            # Portföy katkısı (Ağırlık * Değişim)
            weight = h["market_value"] / total_value_now
            weighted_daily_sum += d_chg * weight
            weighted_weekly_sum += w_chg * weight
            weighted_monthly_sum += m_chg * weight

            asset_details.append({
                "symbol": h["symbol"],
                "daily_chg": d_chg,
                "weekly_chg": w_chg,
                "monthly_chg": m_chg,
                "yearly_chg": y_chg
            })
            
        return {
            "portfolio_summary": {
                "total_value": total_value_now,
                "daily_return": weighted_daily_sum,
                "weekly_return": weighted_weekly_sum,
                "monthly_return": weighted_monthly_sum
            },
            "asset_details": asset_details
        }

    def _analyze_lots(self, user_id, holdings):
        """
        Parçalı Maliyet Analizi:
        Hangi tarihte kaç TL'den alındı ve o spesifik alımın kar/zarar durumu nedir?
        """
        lot_details = []
        
        for h in holdings:
            # Sadece "ALIM" işlemlerini getir
            transactions = self.db.query(Transaction).filter(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.security_id == h["security_id"],
                    Transaction.side == "BUY"
                )
            ).order_by(Transaction.trade_date.desc()).all()
            
            tx_breakdown = []
            for tx in transactions:
                buy_price = float(tx.price)
                current_price = h["current_price"]
                
                pl_percent = ((current_price - buy_price) / buy_price) * 100
                
                tx_breakdown.append({
                    "date": tx.trade_date.strftime("%Y-%m-%d"),
                    "quantity": float(tx.quantity),
                    "buy_price": buy_price,
                    "pl_percent": pl_percent,
                    "status": "KAR" if pl_percent > 0 else "ZARAR"
                })
            
            lot_details.append({
                "symbol": h["symbol"],
                "current_price": h["current_price"],
                "avg_cost": h["avg_cost"],
                "avg_pl_percent": ((h["current_price"] - h["avg_cost"]) / h["avg_cost"]) * 100,
                "transactions": tx_breakdown
            })
            
        return lot_details

    def _calculate_weights(self, holdings):
        """Portföy Dağılımı (Pasta Grafik Verisi)"""
        total_val = sum(h["market_value"] for h in holdings)
        allocation = []
        for h in holdings:
            ratio = (h["market_value"] / total_val) * 100
            allocation.append({
                "symbol": h["symbol"],
                "weight": ratio,
                "value": h["market_value"]
            })
        # Ağırlığa göre sırala (Büyükten küçüğe)
        allocation.sort(key=lambda x: x["weight"], reverse=True)
        return allocation

    def _calculate_extremes(self, holdings):
        """En İyi ve En Kötü Performanslar (Etiket Kontrollü)"""
        # Kar/Zarar Yüzdesine göre sırala
        sorted_holdings = sorted(holdings, key=lambda x: (x["current_price"] - x["avg_cost"]) / x["avg_cost"], reverse=True)
        
        if not sorted_holdings:
            return None

        best = sorted_holdings[0]
        worst = sorted_holdings[-1]
        
        # En kötü performansın yüzdesini hesapla
        worst_pl_pct = ((worst["current_price"] - worst["avg_cost"]) / worst["avg_cost"]) * 100
        
        # --- DÜZELTME: EĞER ZARAR YOKSA ETİKETİ DEĞİŞTİR ---
        if worst_pl_pct >= 0:
            worst_label = "En Az Getiri"
            is_loss = False
        else:
            worst_label = "Kaybettiren"
            is_loss = True
            
        def format_stats(item):
            pl_pct = ((item["current_price"] - item["avg_cost"]) / item["avg_cost"]) * 100
            return f"{item['symbol']} (%{pl_pct:.2f})"

        return {
            "best_performer": format_stats(best),
            "worst_performer": format_stats(worst),
            "worst_label": worst_label, # Dinamik Etiket
            "worst_is_loss": is_loss    # Renklendirme için bayrak
        }