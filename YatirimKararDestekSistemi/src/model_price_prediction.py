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
    def __init__(self, n_future=10):
        self.n_future = n_future

    def predict_trend_prophet(self, df):
        prophet_df = df.reset_index()[["Tarih", "Kapanış"]]
        prophet_df.columns = ["ds", "y"]
        
        model = Prophet(daily_seasonality=True)
        model.fit(prophet_df)
        
        future = model.make_future_dataframe(periods=self.n_future, freq='B')
        forecast = model.predict(future)
        
        result = forecast[["ds", "yhat"]].copy()
        result.rename(columns={"ds": "Tarih", "yhat": "Tahmin_Prophet"}, inplace=True)
        result.set_index("Tarih", inplace=True)
        return result

    def predict_trend_arima(self, df):
        model = auto_arima(df["Kapanış"], seasonal=False, trace=False, error_action='ignore', suppress_warnings=True)
        forecast = model.predict(n_periods=self.n_future)
        
        last_date = df.index[-1]
        future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=self.n_future, freq='B')
        return pd.DataFrame({"Tahmin_ARIMA": forecast.values}, index=future_dates)

    def predict_ml_models(self, df, future_dates):
        ml_engine = MLEngine(df, n_future=self.n_future)
        ml_results = ml_engine.run_all_models()
        ml_results.index = future_dates
        return ml_results

    def predict_volatility_garch(self, returns):
        model = arch_model(returns, vol='Garch', p=1, q=1, dist='Normal')
        res = model.fit(disp="off")
        forecast = res.forecast(horizon=self.n_future)
        return np.sqrt(forecast.variance.values[-1, :])

    def run_hybrid_forecast(self, df):
        # 1. TS Modelleri
        prophet_res = self.predict_trend_prophet(df)
        arima_res = self.predict_trend_arima(df)
        
        # 2. ML Modelleri
        future_dates = arima_res.index
        ml_res = self.predict_ml_models(df, future_dates)
        
        # 3. Volatilite
        vol_forecast = self.predict_volatility_garch(df["log_return"])
        
        # 4. Birleştirme (Tüm sütunları koruyoruz)
        final_df = arima_res.join(prophet_res, how="left") # Önce TS
        final_df = final_df.join(ml_res, how="left")       # Sonra ML
        
        # Ensemble Hesaplamaları
        final_df["TS_Ensemble"] = (final_df["Tahmin_ARIMA"] + final_df["Tahmin_Prophet"]) / 2
        
        ml_cols = ["Tahmin_SVR", "Tahmin_RandomForest", "Tahmin_LightGBM"]
        final_df["ML_Ensemble"] = final_df[ml_cols].mean(axis=1)
        
        # Ağırlıklı Final Karar (TS %80 - ML %20)
        final_df["Final_Ensemble"] = (final_df["TS_Ensemble"] * 0.80) + (final_df["ML_Ensemble"] * 0.20)
        
        final_df["Tahmin_Volatilite"] = vol_forecast
        
        return final_df