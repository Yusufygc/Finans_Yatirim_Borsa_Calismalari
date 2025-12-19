import yfinance as yf
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import and_
from src.data.models import Security, PriceHistory

class MarketDataService:
    """
    Piyasa verilerini (yfinance) çeker ve veritabanını günceller.
    Otomatik eksik veri tamamlama özelliğine sahiptir.
    """
    def __init__(self, db: Session):
        self.db = db

    def get_ticker_info(self, symbol: str):
        """
        Tek bir hissenin anlık/günlük verisini yfinance'dan çeker.
        Veritabanına YAZMAZ, sadece UI'da göstermek içindir.
        """
        yf_symbol = symbol if ".IS" in symbol or symbol == "USDTRY" else f"{symbol}.IS"
        
        try:
            ticker = yf.Ticker(yf_symbol)
            # Son 1 günlük veriyi al
            hist = ticker.history(period="1d")
            
            if hist.empty:
                return None
            
            # Pandas Series olarak son satırı (bugünü) al
            latest = hist.iloc[-1]
            
            return {
                "date": latest.name.date(),
                "open": float(latest["Open"]),
                "high": float(latest["High"]),
                "low": float(latest["Low"]),
                "close": float(latest["Close"]),
                "volume": int(latest["Volume"])
            }
        except Exception as e:
            print(f"[HATA] {symbol} anlık verisi çekilirken hata: {e}")
            return None

    def update_price_history(self, symbol: str):
        """
        Verilen sembolün fiyatını çeker ve PriceHistory tablosuna yazar.
        Eğer hisse yeniyse veya verisi azsa geçmiş 2 yılı çeker.
        """
        # 1. Hisseni DB'den bul veya Yarat
        security = self.db.query(Security).filter(Security.symbol == symbol).first()
        if not security:
            security = Security(symbol=symbol, name=symbol)
            self.db.add(security)
            self.db.commit()
            print(f"[BİLGİ] Yeni hisse tanımlandı: {symbol}")

        # 2. Mevcut Veri Sayısını Kontrol Et (Akıllı Güncelleme)
        existing_count = self.db.query(PriceHistory).filter(
            PriceHistory.security_id == security.id
        ).count()

        # Eğer veri azsa (yeni hisse) 2 yıllık, çoksa sadece son 5 günü çek
        fetch_period = "2y" if existing_count < 200 else "5d"
        
        print(f"[BİLGİ] {symbol} için veri çekiliyor (Periyot: {fetch_period})...")

        # 3. yfinance'dan Veri Çek
        yf_symbol = symbol if ".IS" in symbol or symbol == "USDTRY" else f"{symbol}.IS"
        
        try:
            ticker = yf.Ticker(yf_symbol)
            hist = ticker.history(period=fetch_period)
            
            if hist.empty:
                print(f"[UYARI] {symbol} için yfinance verisi boş döndü.")
                return None
            
            # 4. Veritabanına Yaz (Bulk Insert/Update Mantığı)
            added_count = 0
            updated_count = 0

            for index, row in hist.iterrows():
                date_val = index.date()
                
                # O tarihli kayıt var mı?
                existing_record = self.db.query(PriceHistory).filter(
                    and_(
                        PriceHistory.security_id == security.id,
                        PriceHistory.date == date_val
                    )
                ).first()

                if existing_record:
                    # Canlı veri geliyorsa gün içindeki değişimi güncelle
                    # Sadece son günün verisini güncellemek performans için iyidir
                    if date_val == date.today() or fetch_period == "5d":
                        existing_record.close_price = float(row["Close"])
                        existing_record.high_price = float(row["High"])
                        existing_record.low_price = float(row["Low"])
                        existing_record.open_price = float(row["Open"])
                        existing_record.volume = int(row["Volume"])
                        updated_count += 1
                else:
                    # Kayıt yoksa ekle
                    new_price = PriceHistory(
                        security_id=security.id,
                        date=date_val,
                        open_price=float(row["Open"]),
                        high_price=float(row["High"]),
                        low_price=float(row["Low"]),
                        close_price=float(row["Close"]),
                        volume=int(row["Volume"])
                    )
                    self.db.add(new_price)
                    added_count += 1

            self.db.commit()
            
            if not hist.empty:
                last_price = hist["Close"].iloc[-1]
                print(f"[TAMAMLANDI] {symbol}: {added_count} yeni kayıt, {updated_count} güncelleme. Son Fiyat: {last_price:.2f}")
                return last_price
            return 0.0

        except Exception as e:
            self.db.rollback()
            print(f"[HATA] {symbol} verisi güncellenirken hata: {e}")
            return None

    def update_all_tickers(self):
        """
        Sistemdeki tüm hisseleri toplu günceller.
        """
        securities = self.db.query(Security).all()
        print(f"\n--- Piyasa Verileri Güncelleniyor ({len(securities)} Hisse) ---")
        
        for sec in securities:
            self.update_price_history(sec.symbol)
            
        print("--- Güncelleme Tamamlandı ---\n")