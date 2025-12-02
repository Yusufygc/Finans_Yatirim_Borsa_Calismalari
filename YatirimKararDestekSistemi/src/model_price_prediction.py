import pandas as pd
import numpy as np
import os
import joblib
from prophet import Prophet
from arch import arch_model
from pmdarima import auto_arima
from ml_models import MLEngine
import warnings

pd.options.display.float_format = '{:,.2f}'.format
warnings.filterwarnings('ignore')

class HybridModel:
    def __init__(self, n_future=10):
        self.n_future = n_future
        self.prophet_model = None
        self.arima_model = None
        self.ml_engine = None

    def save_trained_models(self, ticker):
        """
        Eğitilmiş modelleri Proje Ana Dizinindeki 'models/{ticker}/' klasörüne kaydeder.
        """
        # Şu anki dosyanın (model_price_prediction.py) bulunduğu tam yolu al
        current_file_path = os.path.abspath(__file__)
        
        # Bu dosyanın bulunduğu klasör (src/)
        src_directory = os.path.dirname(current_file_path)
        
        # src'nin bir üst dizini (Proje Ana Dizini / Root)
        project_root = os.path.dirname(src_directory)
        
        # models klasörünün yolu: ProjeRoot/models
        base_dir = os.path.join(project_root, "models")
        
        # Hisseye özel klasör (Örn: ProjeRoot/models/ASELS)
        ticker_dir = os.path.join(base_dir, ticker)

        # Klasör yoksa oluştur (Recursive olarak)
        if not os.path.exists(ticker_dir):
            os.makedirs(ticker_dir)
            
        print(f"\n[KAYIT] Modeller '{ticker_dir}' klasörüne kaydediliyor...")
        
        # 1. Prophet Kayıt
        if self.prophet_model:
            joblib.dump(self.prophet_model, os.path.join(ticker_dir, "prophet_model.pkl"))
            print("   -> Prophet kaydedildi.")
            
        # 2. ARIMA Kayıt
        if self.arima_model:
            joblib.dump(self.arima_model, os.path.join(ticker_dir, "arima_model.pkl"))
            print("   -> ARIMA kaydedildi.")
            
        # 3. ML Modelleri Kayıt (SVR, RF, LightGBM)
        if self.ml_engine and self.ml_engine.trained_models:
            for name, model in self.ml_engine.trained_models.items():
                filename = f"{name.lower()}_model.pkl"
                joblib.dump(model, os.path.join(ticker_dir, filename))
                print(f"   -> {name} kaydedildi.")
                
        print(f"[BAŞARILI] Tüm modeller yedeklendi.\n")

    def predict_trend_prophet(self, df):
        prophet_df = df.reset_index()[["Tarih", "Kapanış"]]
        prophet_df.columns = ["ds", "y"]
        
        self.prophet_model = Prophet(daily_seasonality=True)
        self.prophet_model.fit(prophet_df)
        
        future = self.prophet_model.make_future_dataframe(periods=self.n_future, freq='B')
        forecast = self.prophet_model.predict(future)
        
        result = forecast[["ds", "yhat"]].copy()
        result.rename(columns={"ds": "Tarih", "yhat": "Tahmin_Prophet"}, inplace=True)
        result.set_index("Tarih", inplace=True)
        return result

    def predict_trend_arima(self, df):
        self.arima_model = auto_arima(df["Kapanış"], seasonal=False, trace=False, error_action='ignore', suppress_warnings=True)
        forecast = self.arima_model.predict(n_periods=self.n_future)
        
        last_date = df.index[-1]
        future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=self.n_future, freq='B')
        return pd.DataFrame({"Tahmin_ARIMA": forecast.values}, index=future_dates)

    def predict_ml_models(self, df, future_dates):
        self.ml_engine = MLEngine(df, n_future=self.n_future)
        ml_results = self.ml_engine.run_all_models()
        ml_results.index = future_dates
        return ml_results

    def predict_volatility_garch(self, returns):
        model = arch_model(returns, vol='Garch', p=1, q=1, dist='Normal')
        res = model.fit(disp="off")
        forecast = res.forecast(horizon=self.n_future)
        return np.sqrt(forecast.variance.values[-1, :])

    def run_hybrid_forecast(self, df, save_models=False, ticker="Unknown"):
        print(f"\n>> {self.n_future} GÜNLÜK TAHMİN MOTORU ÇALIŞIYOR...")
        
        # 1. TS Modelleri
        prophet_res = self.predict_trend_prophet(df)
        arima_res = self.predict_trend_arima(df)
        
        # 2. ML Modelleri
        future_dates = arima_res.index
        ml_res = self.predict_ml_models(df, future_dates)
        
        # 3. Volatilite
        vol_forecast = self.predict_volatility_garch(df["log_return"])
        
        # Modelleri kaydetme isteği varsa kaydet
        if save_models:
            self.save_trained_models(ticker)
        
        # 4. Birleştirme
        final_df = arima_res.join(prophet_res, how="left")
        final_df = final_df.join(ml_res, how="left")
        
        # Ensemble Hesaplamaları
        final_df["TS_Ensemble"] = (final_df["Tahmin_ARIMA"] + final_df["Tahmin_Prophet"]) / 2
        
        ml_cols = ["Tahmin_SVR", "Tahmin_RandomForest", "Tahmin_LightGBM"]
        final_df["ML_Ensemble"] = final_df[ml_cols].mean(axis=1)
        
        # TS Ağırlıklı (%80) Final Karar
        final_df["Final_Ensemble"] = (final_df["TS_Ensemble"] * 0.80) + (final_df["ML_Ensemble"] * 0.20)
        final_df["Tahmin_Volatilite"] = vol_forecast
        
        return final_df