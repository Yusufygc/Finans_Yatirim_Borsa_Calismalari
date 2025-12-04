import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error
from ai_core.model_price_prediction import HybridModel

class ModelEvaluator:
    def __init__(self, df, test_days=30):
        self.df = df
        self.test_days = test_days
        self.train_df = df.iloc[:-test_days].copy()
        self.test_df = df.iloc[-test_days:].copy()
        
    def evaluate(self):
        print(f"\n{'='*60}")
        print(f"   BACKTEST RAPORU (Son {self.test_days} Günlük Performans)")
        print(f"{'='*60}")
        print(f"[TEST] Eğitim Verisi: ... - {self.train_df.index[-1].date()}")
        print(f"[TEST] Test Verisi  : {self.test_df.index[0].date()} - {self.test_df.index[-1].date()}")

        # Backtest sırasında model kaydetmeye gerek yok (save_models=False)
        model = HybridModel(n_future=self.test_days)
        results = model.run_hybrid_forecast(self.train_df, save_models=False)
        
        actual = self.test_df["Kapanış"]
        predicted = results["Final_Ensemble"]
        
        rmse = np.sqrt(mean_squared_error(actual, predicted))
        mape = mean_absolute_percentage_error(actual, predicted) * 100
        
        actual_diff = np.diff(actual)
        pred_diff = np.diff(predicted)
        acc = np.mean(np.sign(actual_diff) == np.sign(pred_diff)) * 100
        
        print("\n[METRİKLER]")
        print(f"   -> RMSE (Hata Payı)     : ±{rmse:.2f} TL")
        print(f"   -> MAPE (Yüzdesel Hata) : %{mape:.2f}")
        print(f"   -> Yön Doğruluğu        : %{acc:.1f}")
        print("-" * 60)