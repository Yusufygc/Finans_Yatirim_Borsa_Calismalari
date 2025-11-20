import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.metrics import mean_absolute_error, mean_squared_error


# ========================================
# 1) TÜM MODELLERİ ÇALIŞTIRAN PIPELINE
# ========================================
def forecast_pipeline(df, target_col="Kapanış", days_ahead=7):
    df = df.copy()

    # Eğitim verisi tüm veri
    train = df[target_col]

    # ------------------------
    # ARIMA Modeli
    # ------------------------
    arima_model = ARIMA(train, order=(5, 1, 2))
    arima_fit = arima_model.fit()
    arima_pred = arima_fit.forecast(steps=days_ahead)

    # ------------------------
    # SARIMA Modeli
    # ------------------------
    sarima_model = SARIMAX(train, order=(2, 1, 2), seasonal_order=(1, 1, 1, 12))
    sarima_fit = sarima_model.fit(disp=False)
    sarima_pred = sarima_fit.forecast(steps=days_ahead)

    # ------------------------
    # Holt-Winters
    # ------------------------
    hw_model = ExponentialSmoothing(train, trend="add", seasonal=None)
    hw_fit = hw_model.fit()
    hw_pred = hw_fit.forecast(days_ahead)

    # ------------------------
    # Tüm Tahminleri DataFrame Olarak Döndür
    # ------------------------
    preds = pd.DataFrame({
        "ARIMA": arima_pred,
        "SARIMA": sarima_pred,
        "HoltWinters": hw_pred
    })

    preds.index = pd.date_range(start=df.index[-1] + pd.Timedelta(days=1), periods=days_ahead)

    return preds


# ========================================
# 2) VERİYİ YÜKLE
# ========================================
df = pd.read_csv("D:\\1KodCalismalari\\Projeler\\Finans_Yatirim_Borsa_Calismalari\\DatasetOlusturma\\Dataset\\ASELS.csv")
df["Tarih"] = pd.to_datetime(df["Tarih"], dayfirst=True)
df.set_index("Tarih", inplace=True)
df = df[["Kapanış"]].dropna()


# ========================================
# 3) 7 GÜNLÜK İLERİ TAHMİN
# ========================================
preds_7 = forecast_pipeline(df, days_ahead=7)
preds_7.to_csv("tahmin_7gun.csv", encoding="utf-8-sig")

print("\n--- 7 Günlük Tahminler ---")
print(preds_7)


# ========================================
# 4) 30 GÜNLÜK İLERİ TAHMİN
# ========================================
preds_30 = forecast_pipeline(df, days_ahead=30)
preds_30.to_csv("tahmin_30gun.csv", encoding="utf-8-sig")

print("\n--- 30 Günlük Tahminler ---")
print(preds_30)


# ========================================
# 5) GRAFİKLE SONUÇLARIN GÖSTERİMİ
# ========================================
plt.figure(figsize=(14, 7))
plt.plot(df["Kapanış"], label="Gerçek Veriler", color="black")
plt.plot(preds_30.index, preds_30["ARIMA"], label="ARIMA 30G Tahmin")
plt.plot(preds_30.index, preds_30["SARIMA"], label="SARIMA 30G Tahmin")
plt.plot(preds_30.index, preds_30["HoltWinters"], label="Holt-Winters 30G Tahmin")

plt.title("ASELS – 30 Günlük İleri Tahmin (Geleneksel Zaman Serisi Modelleri)")
plt.xlabel("Tarih")
plt.ylabel("Kapanış Fiyatı")
plt.legend()
plt.grid()
plt.show()

print("\nTahmin dosyaları başarıyla oluşturuldu: tahmin_7gun.csv, tahmin_30gun.csv")
