import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.metrics import mean_squared_error, mean_absolute_error

# ======================================
# 1. VERİYİ YÜKLE
# ======================================
df = pd.read_csv("D:\\1KodCalismalari\\Projeler\\Finans_Yatirim_Borsa_Calismalari\\DatasetOlusturma\\Dataset\\ASELS.csv")   # <-- kendi dosya adını yaz
df["Tarih"] = pd.to_datetime(df["Tarih"], dayfirst=True)

# Tarihi index yap
df.set_index("Tarih", inplace=True)

# Sadece kapanış fiyatı ile çalış
df = df[["Kapanış"]]
df.dropna(inplace=True)

# ======================================
# 2. TRAIN / TEST AYRIMI
# ======================================
train = df[:-60]
test = df[-60:]

# ======================================
# 3. ARIMA MODELİ
# ======================================
print("ARIMA modeli eğitiliyor...")
arima_model = ARIMA(train["Kapanış"], order=(5,1,2))
arima_fit = arima_model.fit()
arima_pred = arima_fit.forecast(len(test))

# ======================================
# 4. SARIMA MODELİ
# ======================================
print("SARIMA modeli eğitiliyor...")
sarima_model = SARIMAX(train["Kapanış"], order=(2,1,2), seasonal_order=(1,1,1,12))
sarima_fit = sarima_model.fit(disp=False)
sarima_pred = sarima_fit.forecast(len(test))

# ======================================
# 5. HOLT-WINTERS
# ======================================
print("Holt-Winters modeli eğitiliyor...")
hw_model = ExponentialSmoothing(train["Kapanış"], trend="add", seasonal=None)
hw_fit = hw_model.fit()
hw_pred = hw_fit.forecast(len(test))

# ======================================
# 6. PERFORMANS KARŞILAŞTIRMASI
# ======================================
def evaluate(y_true, y_pred, name):
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    print(f"{name} -> MAE: {mae:.4f}, RMSE: {rmse:.4f}")

print("\n--- MODEL PERFORMANSLARI ---\n")
evaluate(test["Kapanış"], arima_pred, "ARIMA")
evaluate(test["Kapanış"], sarima_pred, "SARIMA")
evaluate(test["Kapanış"], hw_pred, "Holt-Winters")

# ======================================
# 7. GRAFİK
# ======================================
plt.figure(figsize=(12,6))
plt.plot(train["Kapanış"], label="Eğitim Verisi")
plt.plot(test["Kapanış"], label="Gerçek Test Verisi", color="black")
plt.plot(test.index, arima_pred, label="ARIMA Tahmin")
plt.plot(test.index, sarima_pred, label="SARIMA Tahmin")
plt.plot(test.index, hw_pred, label="Holt-Winters Tahmin")

plt.title("ASELS – Geleneksel Zaman Serisi Modelleri Tahmin Sonuçları")
plt.xlabel("Tarih")
plt.ylabel("Kapanış Fiyatı")
plt.legend()
plt.grid()
plt.show()
