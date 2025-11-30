import pandas as pd
import numpy as np
import os
# import yfinance as yf # İnternet erişimi varsa aktif edilebilir

class DataLoader:
    """
    CSV dosyasından veya yfinance üzerinden veri çeker.
    """
    def __init__(self, file_path=None, ticker=None):
        self.file_path = file_path
        self.ticker = ticker

    def load_data(self):
        # 1. Öncelik: CSV Dosyası
        if self.file_path and os.path.exists(self.file_path):
            print(f"[INFO] Veri CSV'den yükleniyor: {self.file_path}")
            df = pd.read_csv(self.file_path)
            df["Tarih"] = pd.to_datetime(df["Tarih"], dayfirst=True)
            df.set_index("Tarih", inplace=True)
        
        # 2. Öncelik: yfinance (Eğer CSV yoksa ve ticker verildiyse)
        # elif self.ticker:
        #     print(f"[INFO] {self.ticker} için Yahoo Finance verisi çekiliyor...")
        #     df = yf.download(self.ticker, period="5y", interval="1d")
        #     df.reset_index(inplace=True)
        #     df.rename(columns={"Date": "Tarih", "Close": "Kapanış", "Open": "Açılış", "High": "Yüksek", "Low": "Düşük", "Volume": "Hacim"}, inplace=True)
        #     df.set_index("Tarih", inplace=True)
        
        else:
            raise FileNotFoundError("Veri kaynağı bulunamadı (CSV yolu veya Ticker girilmeli).")

        # Veri Temizleme ve Hazırlık
        df = df.asfreq("B")
        
        if "Kapanış" not in df.columns and "Close" in df.columns:
            df["Kapanış"] = df["Close"]
            
        df["Kapanış"] = df["Kapanış"].interpolate()
        
        # Logaritmik Getiri
        df["log_close"] = np.log(df["Kapanış"])
        df["log_return"] = df["log_close"].diff() * 100 
        df.dropna(inplace=True)
        
        print(f"[INFO] Veri hazır. Son Tarih: {df.index[-1].strftime('%Y-%m-%d')}")
        return df