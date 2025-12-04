import numpy as np
import pandas as pd
from sklearn.svm import SVR
from sklearn.ensemble import RandomForestRegressor
from lightgbm import LGBMRegressor
from sklearn.preprocessing import StandardScaler
import warnings

warnings.filterwarnings('ignore')

class MLEngine:
    """
    SVR, Random Forest ve LightGBM modellerini çalıştırır.
    GÜNCELLEME: Basit Lag yerine 'Sliding Window' (Kayan Pencere) yöntemi eklendi.
    """
    def __init__(self, df, n_future=10, window_size=30):
        self.df = df.copy()
        self.n_future = n_future
        self.window_size = window_size # Geçmişe ne kadar bakacağı (Örn: 30 gün)
        self.scalers = {} 
        self.trained_models = {} 
        
        self.models = {
            "SVR": SVR(kernel='rbf', C=100, gamma=0.1, epsilon=.1),
            "RandomForest": RandomForestRegressor(n_estimators=100, random_state=42),
            "LightGBM": LGBMRegressor(n_estimators=100, random_state=42, verbose=-1)
        }

    def create_windowed_dataset(self, data):
        """
        Veriyi pencereleme yöntemiyle (X, y) formatına çevirir.
        X: [t-30, t-29, ..., t-1] (Girdi: Son 30 gün)
        y: [t] (Hedef: Bugün)
        """
        X, y = [], []
        # Veriyi numpy array'e çevir
        data_array = data.values
        
        for i in range(self.window_size, len(data_array)):
            X.append(data_array[i-self.window_size:i, 0])
            y.append(data_array[i, 0])
            
        return np.array(X), np.array(y)

    def predict_recursive(self, model_name, model, last_window):
        """
        Geleceği yinelemeli (recursive) tahmin eder.
        """
        predictions = []
        current_window = last_window.reshape(1, -1) # (1, 30) boyutunda
        
        for _ in range(self.n_future):
            # SVR için ölçekleme kontrolü
            if model_name == "SVR":
                current_window_scaled = self.scalers[model_name][0].transform(current_window)
                pred_scaled = model.predict(current_window_scaled)
                pred = self.scalers[model_name][1].inverse_transform(pred_scaled.reshape(-1, 1)).item()
            else:
                pred = model.predict(current_window).item()
            
            predictions.append(pred)
            
            # Pencereyi kaydır: En eski günü at, yeni tahmini sona ekle
            # [t-29, ..., t-1, tahmini_t] -> Yeni girdi bu olacak
            new_window = np.roll(current_window, -1)
            new_window[0, -1] = pred 
            current_window = new_window
            
        return predictions

    def run_all_models(self):
        print(f"   -> ML Modelleri eğitiliyor (Window Size: {self.window_size})...")
        
        # Sadece Kapanış fiyatını al
        data = self.df[["Kapanış"]]
        
        # Pencereleme ile veri seti oluştur
        X, y = self.create_windowed_dataset(data)
        
        # Son bilinen pencere (Gelecek tahmini için başlangıç noktası)
        last_window = data.values[-self.window_size:]
        
        results = {}
        for name, model in self.models.items():
            # SVR için ölçekleme
            if name == "SVR":
                scaler_X = StandardScaler()
                scaler_y = StandardScaler()
                X_scaled = scaler_X.fit_transform(X)
                y_scaled = scaler_y.fit_transform(y.reshape(-1, 1)).ravel()
                
                model.fit(X_scaled, y_scaled)
                self.scalers[name] = (scaler_X, scaler_y)
            else:
                model.fit(X, y)
            
            # Modeli kaydet (Hafızada)
            self.trained_models[name] = model
            
            # Tahmin yap
            preds = self.predict_recursive(name, model, last_window)
            results[f"Tahmin_{name}"] = preds
            
        return pd.DataFrame(results)