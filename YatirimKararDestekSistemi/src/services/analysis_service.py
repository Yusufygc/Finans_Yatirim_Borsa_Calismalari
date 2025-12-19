import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import date
from src.data.models import Security, PriceHistory, AiPrediction, PortfolioHolding, User

# AI Core Modüllerini Dahil Ediyoruz
# Not: ai_core içindeki sınıfları doğrudan kullanıyoruz (Pipeline dosyasını bypass ediyoruz)
try:
    from src.ai_core.feature_engineering import FeatureEngineer
    from src.ai_core.model_price_prediction import HybridModel
    from src.ai_core.risk_profile import RiskManager
except ImportError:
    print("[UYARI] AI Core modülleri bulunamadı. Analiz servisi sınırlı çalışacak.")

class AnalysisService:
    def __init__(self, db: Session):
        self.db = db

    def _get_price_history_df(self, security_id: int, limit: int = 500):
        """
        Veritabanından fiyat geçmişini çeker ve Pandas DataFrame'e çevirir.
        ai_core modülleri DataFrame beklediği için bu dönüşüm şarttır.
        """
        # Tarihe göre sıralı çek (Eskiden yeniye)
        history = self.db.query(PriceHistory).filter(
            PriceHistory.security_id == security_id
        ).order_by(PriceHistory.date.desc()).limit(limit).all()

        if not history:
            return None

        # Tersten sırala (Eskiden yeniye doğru olması lazım)
        history.reverse()

        data = []
        for h in history:
            data.append({
                "Tarih": h.date,
                "Open": float(h.open_price) if h.open_price else 0,
                "High": float(h.high_price) if h.high_price else 0,
                "Low": float(h.low_price) if h.low_price else 0,
                "Kapanış": float(h.close_price), # ai_core 'Kapanış' veya 'Close' bekler
                "Volume": int(h.volume) if h.volume else 0
            })
        
        # Veriyi çekip listeye attıktan sonra:
        df = pd.DataFrame(data)
        if df.empty:
            return None
            
        df["Tarih"] = pd.to_datetime(df["Tarih"])
        df.set_index("Tarih", inplace=True)
        
        # TEKİLLEŞTİRME (Kritik Düzeltme)
        # Aynı tarihte birden fazla kayıt varsa sonuncusunu tut
        df = df[~df.index.duplicated(keep='last')]
        
        return df

    def run_prediction(self, symbol: str, risk_profile: str = "orta"):
        """
        Tek bir hisse için AI tahminlerini çalıştırır ve DB'ye kaydeder.
        """
        print(f"\n[{symbol}] İçin Analiz Başlatılıyor...")
        
        # 1. Hisse ve Veri Kontrolü
        security = self.db.query(Security).filter(Security.symbol == symbol).first()
        if not security:
            print(f"[HATA] {symbol} bulunamadı.")
            return None

        df = self._get_price_history_df(security.id)
        if df is None or len(df) < 50:
            print(f"[HATA] {symbol} için yeterli veri yok (Min 50 gün).")
            return None

        try:
            # 2. Özellik Mühendisliği (Feature Engineering)
            engineer = FeatureEngineer(df)
            df_featured = engineer.create_features() # RSI, MACD, SMA ekler

            # 3. Fiyat Tahmini (Hybrid Model)
            # n_future=5 (5 günlük tahmin yapalım)
            model_engine = HybridModel(n_future=5)
            # Ticker ismini model kaydı için gönderiyoruz
            forecast_df = model_engine.run_hybrid_forecast(df_featured, save_models=True, ticker=symbol)

            # 4. Risk Yönetimi ve Sinyal Üretimi
            risk_man = RiskManager(risk_profile=risk_profile)
            
            current_close = df_featured["Kapanış"].iloc[-1]
            current_rsi = df_featured["RSI"].iloc[-1] if "RSI" in df_featured.columns else 50
            current_sma = df_featured["SMA_50"].iloc[-1] if "SMA_50" in df_featured.columns else current_close

            final_table = risk_man.generate_signals(
                forecast_df, 
                current_price=current_close,
                current_rsi=current_rsi, 
                current_sma=current_sma
            )
            
            # Yarınki tahmini al (İlk satır)
            prediction = final_table.iloc[0]
            
            # 5. Sonucu Veritabanına Kaydet
            # Önce bugüne ait eski tahmin varsa silelim (Tekrar analiz yapılırsa duplicate olmasın)
            existing_pred = self.db.query(AiPrediction).filter(
                AiPrediction.security_id == security.id,
                AiPrediction.prediction_date == date.today()
            ).first()
            
            if existing_pred:
                self.db.delete(existing_pred)

            new_pred = AiPrediction(
                security_id=security.id,
                prediction_date=date.today(),
                target_date=prediction.name.date(), # Pandas index'inden tarihi al
                predicted_price=float(prediction["Final_Ensemble"]),
                model_name="Hybrid_Ensemble_v2",
                confidence_score=0.85, # Şimdilik statik, ileride modelden dönebilir
                signal=prediction["Sinyal"]
            )
            self.db.add(new_pred)
            self.db.commit()
            
            print(f"[BAŞARILI] {symbol} Tahmini: {new_pred.predicted_price:.2f} TL | Sinyal: {new_pred.signal}")
            return new_pred

        except Exception as e:
            self.db.rollback()
            print(f"[HATA] Analiz sırasında hata: {e}")
            return None

    def calculate_portfolio_performance(self, user_id: int):
        """
        Kullanıcının portföyündeki kar/zarar durumunu hesaplar.
        """
        holdings = self.db.query(PortfolioHolding).filter(PortfolioHolding.user_id == user_id).all()
        user = self.db.query(User).filter(User.id == user_id).first()
        
        summary = {
            "total_value": 0.0,
            "total_cost": 0.0,
            "total_pl": 0.0, # Profit/Loss
            "pl_percentage": 0.0,
            "positions": []
        }

        for h in holdings:
            # Güncel fiyatı PriceHistory'den (en son kayıt) çek
            last_price_row = self.db.query(PriceHistory).filter(
                PriceHistory.security_id == h.security_id
            ).order_by(PriceHistory.date.desc()).first()
            
            current_price = float(last_price_row.close_price) if last_price_row else float(h.avg_cost)
            
            qty = float(h.quantity)
            avg_cost = float(h.avg_cost)
            
            market_value = qty * current_price
            cost_basis = qty * avg_cost
            pl = market_value - cost_basis
            pl_pct = (pl / cost_basis * 100) if cost_basis > 0 else 0

            summary["total_value"] += market_value
            summary["total_cost"] += cost_basis
            
            summary["positions"].append({
                "symbol": h.security.symbol,
                "quantity": qty,
                "avg_cost": avg_cost,
                "current_price": current_price,
                "market_value": market_value,
                "pl": pl,
                "pl_pct": pl_pct
            })

        summary["total_pl"] = summary["total_value"] - summary["total_cost"]
        if summary["total_cost"] > 0:
            summary["pl_percentage"] = (summary["total_pl"] / summary["total_cost"]) * 100
            
        return summary