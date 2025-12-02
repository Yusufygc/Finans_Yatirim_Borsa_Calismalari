import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pmdarima import auto_arima

# =======================
# 1. Veriyi Düzenle
# =======================
df = pd.read_csv("D:\\1KodCalismalari\\Projeler\\Finans_Yatirim_Borsa_Calismalari\\DatasetOlusturma\\Dataset\\ASELS.csv")
df["Tarih"] = pd.to_datetime(df["Tarih"], dayfirst=True)
df = df.set_index("Tarih").asfreq("B")

# Eksik günleri doldur
df["Kapanış"] = df["Kapanış"].interpolate()

# Log dönüşümü
df["log_close"] = np.log(df["Kapanış"])

# =======================
# 2. Train-Test böl
# =======================
train = df["log_close"]
n_future = 30

# =======================
# 3. Auto-ARIMA ile en iyi model
# =======================
model = auto_arima(
    train,
    seasonal=False,
    trace=True,
    error_action="ignore",
    suppress_warnings=True
)

print(model.summary())

# =======================
# 4. Tahmin
# =======================
pred_log = model.predict(n_periods=n_future)
future_dates = pd.date_range(df.index[-1] + pd.Timedelta(days=1), periods=n_future, freq="B")

# Log → fiyat dönüşümü
pred_price = np.exp(pred_log)

# Frame haline getir
forecast = pd.DataFrame({
    "Tahmin": pred_price
}, index=future_dates)

print("\n--- 30 Gün Tahmin ---")
print(forecast)

# =======================
# 5. Grafik
# =======================
plt.figure(figsize=(12,6))
plt.plot(df["Kapanış"], label="Gerçek Fiyat")
plt.plot(forecast.index, forecast["Tahmin"], label="Tahmin", color="red")

plt.title("ASELS – Gelişmiş Auto-ARIMA Tahmini (Log + Düzgün Frekans)")
plt.grid()
plt.legend()
plt.show()
