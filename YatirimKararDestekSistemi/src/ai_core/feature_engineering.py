import pandas_ta as ta
import pandas as pd
import numpy as np  # <-- EKLENDİ

class FeatureEngineer:
    """
    Ham fiyat verisine Teknik Analiz indikatörleri ve istatistiksel özellikler ekler.
    """
    def __init__(self, df):
        self.df = df

    def create_features(self):
        print("[INFO] Teknik indikatörler hesaplanıyor...")
        
        if self.df is None or self.df.empty:
            return self.df

        # Sütun adı belirleme (Close mu Kapanış mı?)
        if 'Kapanış' in self.df.columns:
            close_col = 'Kapanış'
        elif 'Close' in self.df.columns:
            close_col = 'Close'
        else:
            close_col = self.df.columns[0]

        # --- 1. Logaritmik Getiri (Model İçin Kritik) ---
        # Formül: ln(Pt / Pt-1)
        try:
            self.df['log_return'] = np.log(self.df[close_col] / self.df[close_col].shift(1))
        except Exception as e:
            print(f"[UYARI] Log getiri hesaplanamadı: {e}")
            self.df['log_return'] = 0.0

        # --- 2. RSI (14 Günlük) ---
        try:
            self.df['RSI'] = self.df.ta.rsi(close=close_col, length=14)
        except Exception:
            self.df['RSI'] = 50.0 

        # --- 3. MACD ---
        try:
            macd = self.df.ta.macd(close=close_col, fast=12, slow=26, signal=9)
            if macd is not None and not macd.empty:
                self.df = pd.concat([self.df, macd], axis=1)
        except Exception:
            pass
        
        # --- 4. Hareketli Ortalamalar (SMA) ---
        data_len = len(self.df)
        try:
            # SMA 50
            if data_len >= 50:
                self.df['SMA_50'] = self.df.ta.sma(close=close_col, length=50)
            else:
                self.df['SMA_50'] = self.df[close_col]

            # SMA 200
            if data_len >= 200:
                self.df['SMA_200'] = self.df.ta.sma(close=close_col, length=200)
            else:
                self.df['SMA_200'] = self.df['SMA_50'] 
        except Exception:
            pass

        # NaN temizliği (Shift işleminden ve indikatör başlangıçlarından doğan boşluklar)
        self.df.dropna(inplace=True)
        
        # Eğer dropna sonrası veri çok azaldıysa uyarı ver
        if len(self.df) < 30:
            print("[UYARI] İndikatör hesaplaması sonrası veri çok azaldı!")

        print(f"[INFO] İndikatörler eklendi. Güncel Boyut: {self.df.shape}")
        return self.df