import pandas as pd
import numpy as np
import os

class DataLoader:
    """
    Sadece yerel CSV dosyasından veri okur ve finansal analiz için hazırlar.
    """
    def __init__(self, file_path):
        self.file_path = file_path

    def load_data(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"[HATA] '{self.file_path}' dosyası bulunamadı!")

        print(f"[INFO] Veri CSV dosyasından yükleniyor: {self.file_path}")
        
        # CSV Okuma
        df = pd.read_csv(self.file_path)
        
        # Tarih Formatı Düzeltme (DD/MM/YYYY veya YYYY-MM-DD)
        try:
            df["Tarih"] = pd.to_datetime(df["Tarih"], dayfirst=True)
        except Exception as e:
            print(f"[UYARI] Tarih formatı algılanamadı, standart format deneniyor: {e}")
            df["Tarih"] = pd.to_datetime(df["Tarih"])
            
        df.set_index("Tarih", inplace=True)
        
        # Sütun isim kontrolü
        if "Kapanış" not in df.columns and "Close" in df.columns:
            df["Kapanış"] = df["Close"]
            
        # Veri Hazırlığı
        df = df.asfreq("B") # İş günleri
        df["Kapanış"] = df["Kapanış"].interpolate() # Eksik verileri doldur
        
        # Logaritmik Getiri
        df["log_close"] = np.log(df["Kapanış"])
        df["log_return"] = df["log_close"].diff() * 100 
        df.dropna(inplace=True)
        
        print(f"[BAŞARILI] Veri Hazır. {df.index[0].date()} - {df.index[-1].date()} (Toplam {len(df)} gün)")
        return df