from sqlalchemy.orm import Session
from .database import SessionLocal, User, Security, PortfolioHolding, AiPrediction, PriceHistory
from datetime import date
from ai_core.pipeline import run_analysis_for_stock
import sys
import os

# ai_core modülünü import edebilmek için yol ayarı
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# AI Modüllerinden gerekli sınıfları çağırıyoruz
# Not: Hata alırsan ilgili dosyaların __init__.py dosyalarının boş olduğundan emin ol
try:
    from ai_core.risk_profile import RiskManager
    # from ai_core.ml_models import EnsembleModel (İleride modelinizi buradan çağıracaksınız)
except ImportError as e:
    print(f"Uyarı: AI modülleri yüklenemedi. {e}")

class PortfolioManager:
    def __init__(self, user_id):
        self.db: Session = SessionLocal()
        self.user = self.db.query(User).filter(User.id == user_id).first()
        if not self.user:
            raise ValueError("Kullanıcı bulunamadı!")
        
        # Kullanıcının risk profiline göre Risk Yöneticisini başlat
        # Eğer users tablosunda risk_profile kolonu yoksa varsayılan 'orta' alınır
        profile = getattr(self.user, 'risk_profile', 'orta')
        self.risk_manager = RiskManager(risk_profile=profile) if 'RiskManager' in globals() else None

    def buy_stock(self, symbol, quantity, price):
        """Hisse Alım İşlemi"""
        sec = self._get_security(symbol)
        
        # Portföyde var mı kontrol et
        holding = self.db.query(PortfolioHolding).filter_by(user_id=self.user.id, security_id=sec.id).first()
        
        if holding:
            # Ağırlıklı ortalama maliyet hesabı
            total_cost = (float(holding.quantity) * float(holding.avg_cost)) + (quantity * price)
            total_qty = float(holding.quantity) + quantity
            holding.avg_cost = total_cost / total_qty
            holding.quantity = total_qty
        else:
            new_holding = PortfolioHolding(user_id=self.user.id, security_id=sec.id, quantity=quantity, avg_cost=price)
            self.db.add(new_holding)
        
        self.db.commit()
        print(f"{symbol} alındı. Yeni Adet: {holding.quantity if holding else quantity}")

    def get_portfolio_summary(self):
        """Portföy Durumunu Listele"""
        holdings = self.user.portfolio_holdings
        print(f"\n--- {self.user.username} Portföy Özeti ---")
        for h in holdings:
            # Burada güncel fiyatı price_history'den veya canlı veriden çekmelisiniz
            # Şimdilik maliyet üzerinden gösteriyoruz
            print(f"Hisse: {h.security.symbol} | Adet: {h.quantity} | Ort. Maliyet: {h.avg_cost}")

    def run_daily_ai_analysis(self):
        """Tüm portföy için AI analizini çalıştırır"""
        print("\n--- Günlük AI Analizi Başlatılıyor ---")
        holdings = self.user.portfolio_holdings
        
        for h in holdings:
            symbol = h.security.symbol
            
            # CSV dosyasının yerini bul (Örn: data/raw/ASELS.csv)
            # Not: Bu path yapısını kendi bilgisayarına göre ayarlamalısın
            file_path = f"D:\\1KodCalismalari\\Projeler\\Finans_Yatirim_Borsa_Calismalari\\YatirimKararDestekSistemi\\data\\raw\\{symbol}.csv"
            
            if not os.path.exists(file_path):
                print(f"HATA: {symbol} için veri dosyası bulunamadı: {file_path}")
                continue

            try:
                # BURADA SENİN ESKİ RUN_PIPELINE MANTIĞINI ÇAĞIRIYORUZ
                # Kullanıcının risk profilini de gönderiyoruz
                analysis_result = run_analysis_for_stock(
                    file_path=file_path, 
                    risk_profile=self.user.risk_profile
                )
                
                predicted_price = analysis_result["predicted_price"]
                signal = analysis_result["signal"]
                reason = analysis_result["reason"]
                
                print(f"Analiz: {symbol} -> Tahmin: {predicted_price:.2f} | Sinyal: {signal} ({reason})")
                
                # Veritabanına Kayıt
                pred = AiPrediction(
                    security_id=h.security_id,
                    target_date=date.today(), 
                    predicted_price=predicted_price,
                    signal=signal,
                    confidence=0.85 # Pipeline'dan güven skoru gelirse buraya ekle
                )
                self.db.add(pred)
                
            except Exception as e:
                print(f"{symbol} analiz edilirken hata oluştu: {e}")
        
        self.db.commit()
        print("Tüm analizler tamamlandı ve veritabanına kaydedildi.")

    def _get_security(self, symbol):
        """Yardımcı fonksiyon: Sembol isminden ID bulur"""
        sec = self.db.query(Security).filter_by(symbol=symbol).first()
        if not sec:
            # Veritabanında yoksa ekleyelim (Demo amaçlı)
            sec = Security(symbol=symbol, name=symbol)
            self.db.add(sec)
            self.db.commit()
        return sec