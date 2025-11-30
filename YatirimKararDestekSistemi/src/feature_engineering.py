import pandas_ta as ta
import pandas as pd

class FeatureEngineer:
    """
    Ham fiyat verisine Teknik Analiz indikatörleri ekler.
    """
    def __init__(self, df):
        self.df = df

    def add_indicators(self):
        print("[INFO] Teknik indikatörler hesaplanıyor...")
        
        # 1. RSI (Relative Strength Index) - 14 Günlük
        self.df['RSI'] = self.df.ta.rsi(close='Kapanış', length=14)
        
        # 2. MACD (Moving Average Convergence Divergence)
        macd = self.df.ta.macd(close='Kapanış', fast=12, slow=26, signal=9)
        self.df = pd.concat([self.df, macd], axis=1)
        
        # 3. Hareketli Ortalamalar (SMA)
        self.df['SMA_50'] = self.df.ta.sma(close='Kapanış', length=50)
        self.df['SMA_200'] = self.df.ta.sma(close='Kapanış', length=200)
        
        # İndikatör hesaplamaları baştaki satırlarda NaN oluşturur, temizleyelim
        self.df.dropna(inplace=True)
        
        print(f"[INFO] İndikatörler eklendi. Güncel Boyut: {self.df.shape}")
        return self.df