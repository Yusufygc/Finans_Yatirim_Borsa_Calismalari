import pandas_ta as ta
import pandas as pd

class FeatureEngineer:
    """
    Ham fiyat verisine Teknik Analiz indikatörleri ekler.
    """
    def __init__(self, df):
        self.df = df

    # Fonksiyon ismini 'add_indicators' yerine 'create_features' yaptık
    # Böylece pipeline.py ile uyumlu hale geldi.
    def create_features(self):
        print("[INFO] Teknik indikatörler hesaplanıyor...")
        
        # Sütun adı kontrolü (Veri setinde İngilizce 'Close' veya Türkçe 'Kapanış' olabilir)
        if 'Kapanış' in self.df.columns:
            close_col = 'Kapanış'
        elif 'Close' in self.df.columns:
            close_col = 'Close'
        else:
            # Eğer ikisi de yoksa varsayılan olarak ilk sütunu almayı denebiliriz veya hata veririz
            print("[UYARI] 'Close' veya 'Kapanış' sütunu bulunamadı. İlk sütun kullanılıyor.")
            close_col = self.df.columns[0]

        # 1. RSI (Relative Strength Index) - 14 Günlük
        self.df['RSI'] = self.df.ta.rsi(close=close_col, length=14)
        
        # 2. MACD (Moving Average Convergence Divergence)
        macd = self.df.ta.macd(close=close_col, fast=12, slow=26, signal=9)
        self.df = pd.concat([self.df, macd], axis=1)
        
        # 3. Hareketli Ortalamalar (SMA)
        self.df['SMA_50'] = self.df.ta.sma(close=close_col, length=50)
        self.df['SMA_200'] = self.df.ta.sma(close=close_col, length=200)
        
        # İndikatör hesaplamaları baştaki satırlarda NaN oluşturur, temizleyelim
        self.df.dropna(inplace=True)
        
        print(f"[INFO] İndikatörler eklendi. Güncel Boyut: {self.df.shape}")
        return self.df