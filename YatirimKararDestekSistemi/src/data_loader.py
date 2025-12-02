import pandas as pd
import numpy as np
import os

class DataLoader:
    """
    Sadece yerel CSV dosyasından veri okur.
    """
    def __init__(self, file_path):
        self.file_path = file_path

    def load_data(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"[HATA] '{self.file_path}' dosyası bulunamadı!")

        print(f"[INFO] Veri CSV dosyasından yükleniyor: {self.file_path}")
        
        df = pd.read_csv(self.file_path)
        
        # Tarih formatı algılama
        try:
            df["Tarih"] = pd.to_datetime(df["Tarih"], dayfirst=True)
        except:
            df["Tarih"] = pd.to_datetime(df["Tarih"])
            
        df.set_index("Tarih", inplace=True)
        
        # Sütun ismi standardizasyonu
        if "Kapanış" not in df.columns and "Close" in df.columns:
            df["Kapanış"] = df["Close"]
            
        # Veri temizleme
        df = df.asfreq("B") # İş günleri
        df["Kapanış"] = df["Kapanış"].interpolate()
        
        # Logaritmik getiri
        df["log_close"] = np.log(df["Kapanış"])
        df["log_return"] = df["log_close"].diff() * 100 
        df.dropna(inplace=True)
        
        print(f"[BAŞARILI] Veri Hazır: {df.index[0].date()} - {df.index[-1].date()} (Toplam {len(df)} gün)")
        return df