import numpy as np
import pandas as pd
from sklearn.svm import SVR
from sklearn.ensemble import RandomForestRegressor
from lightgbm import LGBMRegressor
from sklearn.preprocessing import StandardScaler
import warnings

warnings.filterwarnings('ignore')

class MLEngine:
    def __init__(self, df, n_future=10, lags=5):
        self.df = df.copy()
        self.n_future = n_future
        self.lags = lags 
        self.scalers = {} 
        self.trained_models = {} # Eğitilmiş modelleri burada saklayacağız
        
        self.models = {
            "SVR": SVR(kernel='rbf', C=100, gamma=0.1, epsilon=.1),
            "RandomForest": RandomForestRegressor(n_estimators=100, random_state=42),
            "LightGBM": LGBMRegressor(n_estimators=100, random_state=42, verbose=-1)
        }

    def prepare_data(self):
        data = self.df[["Kapanış"]].copy()
        for lag in range(1, self.lags + 1):
            data[f"Lag_{lag}"] = data["Kapanış"].shift(lag)   
        data.dropna(inplace=True)
        return data

    def predict_recursive(self, model_name, model, train_data, last_known_data):
        X = train_data.drop(columns=["Kapanış"]).values
        y = train_data["Kapanış"].values
        
        # SVR için ölçekleme
        if model_name == "SVR":
            scaler_X = StandardScaler()
            scaler_y = StandardScaler()
            X = scaler_X.fit_transform(X)
            y = scaler_y.fit_transform(y.reshape(-1, 1)).ravel()
            self.scalers[model_name] = (scaler_X, scaler_y)
            
        # Modeli eğit
        model.fit(X, y)
        
        # Eğitilmiş modeli hafızaya al (Kaydetmek için)
        self.trained_models[model_name] = model
        
        # Tahmin döngüsü
        predictions = []
        current_lags = last_known_data.values.reshape(1, -1) 
        
        for _ in range(self.n_future):
            if model_name == "SVR":
                current_lags_scaled = self.scalers[model_name][0].transform(current_lags)
                pred_scaled = model.predict(current_lags_scaled)
                pred = self.scalers[model_name][1].inverse_transform(pred_scaled.reshape(-1, 1)).item()
            else:
                pred = model.predict(current_lags).item()
            
            predictions.append(pred)
            new_lags = np.roll(current_lags, 1)
            new_lags[0, 0] = pred 
            current_lags = new_lags
            
        return predictions

    def run_all_models(self):
        print("   -> ML Modelleri eğitiliyor (SVR, RF, LightGBM)...")
        prepared_data = self.prepare_data()
        last_closes = self.df["Kapanış"].iloc[-self.lags:].values
        current_lags_input = last_closes[::-1] 
        
        results = {}
        for name, model in self.models.items():
            preds = self.predict_recursive(name, model, prepared_data, pd.Series(current_lags_input))
            results[f"Tahmin_{name}"] = preds
            
        return pd.DataFrame(results)