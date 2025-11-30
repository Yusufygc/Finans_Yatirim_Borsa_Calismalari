import pandas as pd
import numpy as np
from prophet import Prophet
from arch import arch_model
from pmdarima import auto_arima
from ml_models import MLEngine
import warnings

pd.options.display.float_format = '{:,.2f}'.format
warnings.filterwarnings('ignore')

class HybridModel:
    """
    Fiyat tahmini için Katmanlı ve Ağırlıklı Ensemble Yapısı:
    DÜZELTME (v2.2): Zaman Serisi (TS) modelleri daha başarılı olduğu için ağırlık TS lehine artırıldı.
    """
    def __init__(self, n_future=10):
        self.n_future = n_future
        self.prophet_model = None
        self.arima_model = None
        self.garch_model_fit = None

    def predict_trend_prophet(self, df):
        prophet_df = df.reset_index()[["Tarih", "Kapanış"]]
        prophet_df.columns = ["ds", "y"]
        
        self.prophet_model = Prophet(daily_seasonality=True)
        self.prophet_model.fit(prophet_df)
        
        future = self.prophet_model.make_future_dataframe(periods=self.n_future, freq='B')
        forecast = self.prophet_model.predict(future)
        
        result = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
        result.rename(columns={
            "ds": "Tarih",
            "yhat": "Tahmin_Prophet",
            "yhat_lower": "Prophet_Alt",
            "yhat_upper": "Prophet_Ust"
        }, inplace=True)
        result.set_index("Tarih", inplace=True)
        return result

    def predict_trend_arima(self, df):
        price_series = df["Kapanış"]
        
        self.arima_model = auto_arima(
            price_series, seasonal=False, trace=False,
            error_action='ignore', suppress_warnings=True, stepwise=True
        )
        
        forecast, conf_int = self.arima_model.predict(n_periods=self.n_future, return_conf_int=True)
        
        last_date = df.index[-1]
        future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=self.n_future, freq='B')
        
        arima_df = pd.DataFrame(index=future_dates)
        arima_df["Tahmin_ARIMA"] = forecast.values
        return arima_df

    def predict_ml_models(self, df, future_dates):
        ml_engine = MLEngine(df, n_future=self.n_future)
        ml_results = ml_engine.run_all_models()
        ml_results.index = future_dates
        return ml_results

    def predict_volatility_garch(self, returns):
        model = arch_model(returns, vol='Garch', p=1, q=1, dist='Normal')
        self.garch_model_fit = model.fit(disp="off")
        
        forecast = self.garch_model_fit.forecast(horizon=self.n_future)
        future_vol = np.sqrt(forecast.variance.values[-1, :])
        return future_vol

    def run_hybrid_forecast(self, df):
        print(f"\n{'='*50}")
        print(f"   {self.n_future} GÜNLÜK TS-ODAKLI ENSEMBLE TAHMİNİ")
        print(f"{'='*50}")
        
        # --- AŞAMA 1: ZAMAN SERİLERİ (Time Series) ---
        print("\n>> [1. KATMAN] Zaman Serisi Modelleri (BASKIN: Ağırlık %80)...")
        prophet_res = self.predict_trend_prophet(df)
        arima_res = self.predict_trend_arima(df)
        
        # Birleştirme
        ts_df = arima_res.join(prophet_res[["Tahmin_Prophet"]], how="left")
        
        # TS Ensemble Hesapla
        ts_df["TS_Ensemble"] = (ts_df["Tahmin_ARIMA"] + ts_df["Tahmin_Prophet"]) / 2
        
        print("\n   >>> Zaman Serisi Sonuçları (İlk 5 Gün):")
        print(ts_df[["Tahmin_ARIMA", "Tahmin_Prophet", "TS_Ensemble"]].head().to_string())

        # --- AŞAMA 2: MAKİNE ÖĞRENİMİ (ML Models) ---
        print("\n>> [2. KATMAN] ML Modelleri (DESTEKLEYİCİ: Ağırlık %20)...")
        future_dates = arima_res.index
        ml_res = self.predict_ml_models(df, future_dates)
        
        # ML Ensemble Hesapla
        ml_cols = [col for col in ml_res.columns if "Tahmin_" in col]
        ml_res["ML_Ensemble"] = ml_res[ml_cols].mean(axis=1)
        
        print("\n   >>> ML Modelleri Sonuçları (İlk 5 Gün):")
        print(ml_res.head().to_string())
        
        # --- AŞAMA 3: VOLATİLİTE (Risk) ---
        print("\n>> [3. AŞAMA] Risk Analizi (GARCH Volatilitesi)...")
        vol_forecast = self.predict_volatility_garch(df["log_return"])
        
        # --- AŞAMA 4: FİNAL BİRLEŞTİRME ---
        print("\n>> [4. AŞAMA] Final Ağırlıklı Birleştirme...")
        
        final_df = ts_df.join(ml_res)
        final_df["Tahmin_Volatilite"] = vol_forecast
        final_df = final_df.join(prophet_res[["Prophet_Alt", "Prophet_Ust"]], how="left")
        
        # ==========================================================
        # DÜZELTİLMİŞ AĞIRLIKLANDIRMA (TS-DRIVEN)
        # ML modelleri (LightGBM/RF) aşırı iyimser (over-optimistic) kaldığı için
        # daha başarılı olan TS modellerine (ARIMA/Prophet) ağırlık veriyoruz.
        # ==========================================================
        
        w_ts = 0.80  # Zaman serisi etkisi artırıldı
        w_ml = 0.20  # ML etkisi düşürüldü
        
        final_df["Final_Ensemble"] = (final_df["TS_Ensemble"] * w_ts) + (final_df["ML_Ensemble"] * w_ml)
        
        print(f"\n[BİLGİ] Modeller birleştirildi (Ağırlıklar -> TS: {w_ts}, ML: {w_ml})")
        return final_df