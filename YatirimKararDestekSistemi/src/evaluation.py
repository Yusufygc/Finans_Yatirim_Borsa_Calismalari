import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error
from model_price_prediction import HybridModel

class ModelEvaluator:
    """
    Modellerin geçmiş performansını ölçer (Backtesting).
    """
    def __init__(self, df, test_days=30):
        self.df = df
        self.test_days = test_days
        
        # Veriyi Eğitim ve Test olarak böl
        self.train_df = df.iloc[:-test_days].copy()
        self.test_df = df.iloc[-test_days:].copy()
        
    def calculate_metrics(self, actual, predicted):
        """
        RMSE, MAPE ve Yön Doğruluğunu hesaplar.
        """
        # RMSE (Kök Ortalama Kare Hata) - TL cinsinden hata
        rmse = np.sqrt(mean_squared_error(actual, predicted))
        
        # MAPE (Ortalama Mutlak Yüzde Hata) - % cinsinden hata
        mape = mean_absolute_percentage_error(actual, predicted) * 100
        
        # Yön Doğruluğu (Directional Accuracy)
        # Fiyatın artış/azalış yönünü doğru bildi mi?
        actual_diff = np.diff(actual)
        pred_diff = np.diff(predicted)
        # İşaretler aynıysa (ikisi de pozitif veya ikisi de negatif) doğrudur
        correct_direction = np.sign(actual_diff) == np.sign(pred_diff)
        accuracy = np.mean(correct_direction) * 100
        
        return {"RMSE": rmse, "MAPE": mape, "Direction_Accuracy": accuracy}

    def evaluate(self):
        print(f"\n{'='*50}")
        print(f"   MODEL PERFORMANS DEĞERLENDİRMESİ (Son {self.test_days} Gün)")
        print(f"{'='*50}")
        
        # Modeli Eğitim setinde kur (Test setini GÖRMEDEN)
        model = HybridModel(n_future=self.test_days)
        
        # Tahmin yap (Sadece eğitim verisini kullanarak)
        # Not: Prophet ve ARIMA'nın eğitim verisine fit edilmesi gerekir.
        # HybridModel yapımız 'run_hybrid_forecast' içinde her seferinde yeniden fit ettiği için
        # sadece train_df'i göndermemiz yeterli.
        
        print(f"[TEST] {self.train_df.index[-1].date()} tarihine kadar eğitiliyor...")
        print(f"[TEST] {self.test_df.index[0].date()} - {self.test_df.index[-1].date()} arası tahmin ediliyor...")
        
        results = model.run_hybrid_forecast(self.train_df)
        
        # Sonuçları Test verisiyle hizala
        comparison = pd.DataFrame()
        comparison["Gerçek"] = self.test_df["Kapanış"]
        # Tahmin sonuçları gelecek tarihli indexlendiği için doğrudan eşleşmeli
        comparison["Tahmin"] = results["Final_Ensemble"]
        
        # Metrikleri Hesapla
        metrics = self.calculate_metrics(comparison["Gerçek"], comparison["Tahmin"])
        
        print("\n   >>> DEĞERLENDİRME SONUÇLARI <<<")
        print(f"   1. Hata Payı (RMSE): ±{metrics['RMSE']:.2f} TL")
        print(f"   2. Yüzdesel Hata (MAPE): %{metrics['MAPE']:.2f}")
        print(f"   3. Yön Tahmin Başarısı: %{metrics['Direction_Accuracy']:.1f}")
        
        # Sharpe Oranı (Tahmini Getiri / Risk)
        # Basitleştirilmiş Sharpe: (Ortalama Günlük Getiri / Getiri Standart Sapması) * sqrt(252)
        returns = comparison["Tahmin"].pct_change().dropna()
        sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() != 0 else 0
        print(f"   4. Model Sharpe Oranı: {sharpe:.2f}")
        
        return metrics