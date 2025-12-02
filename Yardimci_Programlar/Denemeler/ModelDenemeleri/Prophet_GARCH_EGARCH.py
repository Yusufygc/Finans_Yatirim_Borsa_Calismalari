import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from pmdarima import auto_arima
from prophet import Prophet
from arch import arch_model

# =========================
# 1) VERİYİ YÜKLE & HAZIRLA
# =========================
df = pd.read_csv("D:\\1KodCalismalari\\Projeler\\Finans_Yatirim_Borsa_Calismalari\\DatasetOlusturma\\Dataset\\ASELS.csv")

# Tarih kolonunu dönüştür
df["Tarih"] = pd.to_datetime(df["Tarih"], dayfirst=True)

# Tarihi index yap
df.set_index("Tarih", inplace=True)

# Sadece Kapanış ile çalış
df = df[["Kapanış"]].sort_index()
df = df.asfreq("B")              # İş günü frekansı
df["Kapanış"] = df["Kapanış"].interpolate()  # boşluk varsa doldur

# Log fiyat ve getiriler
df["log_close"] = np.log(df["Kapanış"])
df["log_return"] = df["log_close"].diff()
returns = df["log_return"].dropna() * 100    # GARCH için genelde % getiriler kullanılır

# Kaç gün ileri tahmin?
N_FUTURE = 30


# =========================
# 2) AUTO-ARIMA (opsiyonel)
# =========================
def run_auto_arima(series, n_future=30):
    model = auto_arima(
        series,
        seasonal=False,
        trace=True,
        error_action="ignore",
        suppress_warnings=True
    )
    print(model.summary())

    # log seride tahmin et
    pred_log = model.predict(n_periods=n_future)
    future_idx = pd.date_range(series.index[-1] + pd.Timedelta(days=1),
                               periods=n_future, freq="B")
    pred_price = np.exp(pred_log)  # log -> fiyat

    forecast = pd.DataFrame({"ARIMA_Tahmin": pred_price}, index=future_idx)
    return forecast


# =========================
# 3) PROPHET İLE TAHMİN
# =========================
def run_prophet(df_prices, n_future=30):
    # Prophet için ds, y kolonları
    df_p = df_prices.reset_index().rename(columns={"Tarih": "ds", "Kapanış": "y"})
    df_p = df_p[["ds", "y"]]

    m = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False
    )
    m.fit(df_p)

    future = m.make_future_dataframe(periods=n_future, freq="B")
    forecast = m.predict(future)

    # Sadece ileri dönem tahminleri al
    forecast_future = forecast[forecast["ds"] > df_p["ds"].max()].copy()
    forecast_future.set_index("ds", inplace=True)
    forecast_future = forecast_future[["yhat", "yhat_lower", "yhat_upper"]]
    forecast_future.rename(columns={
        "yhat": "Prophet_Tahmin",
        "yhat_lower": "Prophet_AltBand",
        "yhat_upper": "Prophet_UstBand"
    }, inplace=True)

    # Grafik
    m.plot(forecast)
    plt.title("Prophet – ASELS Fiyat Tahmini")
    plt.show()

    return forecast_future


# =========================
# 4) GARCH & EGARCH VOLATİLİTE
# =========================
def run_garch_models(returns, n_future=30):

    # ==========================
    # 1) GARCH(1,1) - normal forecast
    # ==========================
    garch = arch_model(returns, vol="Garch", p=1, q=1, mean="Zero", dist="normal")
    garch_fit = garch.fit(disp="off")
    print(garch_fit.summary())

    garch_forecast = garch_fit.forecast(horizon=n_future)
    garch_var = garch_forecast.variance.iloc[-1].values
    garch_vol = np.sqrt(garch_var)


    # ==========================
    # 2) EGARCH(1,1) - manual multi-step forecast
    # ==========================
    egarch = arch_model(returns, vol="EGARCH", p=1, q=1, mean="Zero", dist="normal")
    egarch_fit = egarch.fit(disp="off")
    print(egarch_fit.summary())

    params = egarch_fit.params
    omega = params["omega"]
    alpha = params["alpha[1]"]
    beta  = params["beta[1]"]
    gamma = params.get("gamma[1]", 0)

    # EGARCH son tahminlerinden başla
    last_sigma2 = egarch_fit.conditional_volatility.iloc[-1] ** 2

    # multi-step forecast (iterative)
    egarch_var = []
    prev_log_sigma2 = np.log(last_sigma2)

    for _ in range(n_future):
        # E[z] = 0, E[|z|] = sqrt(2/pi)
        expected_abs_z = np.sqrt(2/np.pi)
        expected_z = 0

        new_log_sigma2 = (
            omega
            + alpha * expected_abs_z
            + gamma * expected_z
            + beta * prev_log_sigma2
        )

        prev_log_sigma2 = new_log_sigma2
        egarch_var.append(np.exp(new_log_sigma2))

    egarch_vol = np.sqrt(egarch_var)

    # ==========================
    # 3) Return combined dataframe
    # ==========================
    future_idx = pd.date_range(
        returns.index[-1] + pd.Timedelta(days=1),
        periods=n_future,
        freq="B"
    )

    vol_df = pd.DataFrame({
        "GARCH_Volatilite": garch_vol,
        "EGARCH_Volatilite": egarch_vol
    }, index=future_idx)

    return vol_df




# =========================
# 5) MODELLERİ ÇALIŞTIR
# =========================

# Auto-ARIMA (isteğe bağlı)
arima_forecast = run_auto_arima(df["log_close"], n_future=N_FUTURE)

# Prophet fiyat tahmini
prophet_forecast = run_prophet(df[["Kapanış"]], n_future=N_FUTURE)

# GARCH / EGARCH volatilite tahmini
vol_forecast = run_garch_models(returns, n_future=N_FUTURE)

# =========================
# 6) SONUÇLARI BİRLEŞTİR & KAYDET
# =========================
combined = arima_forecast.join(prophet_forecast, how="outer").join(vol_forecast, how="outer")

print("\n--- Birleştirilmiş Tahmin Tablosu (İlk Satırlar) ---")
print(combined.head())

combined.to_csv("tahminler_ARIMA_Prophet_GARCH.csv", encoding="utf-8-sig")

# =========================
# 7) HIZLI GRAFİKLER
# =========================

# Prophet vs Gerçek
plt.figure(figsize=(12,6))
plt.plot(df["Kapanış"], label="Gerçek Fiyat", color="black")
plt.plot(prophet_forecast.index, prophet_forecast["Prophet_Tahmin"], label="Prophet Tahmin", color="blue")
plt.fill_between(
    prophet_forecast.index,
    prophet_forecast["Prophet_AltBand"],
    prophet_forecast["Prophet_UstBand"],
    alpha=0.2, label="Prophet Güven Aralığı"
)
plt.title("ASELS – Prophet Tahmini ve Güven Aralığı")
plt.legend()
plt.grid()
plt.show()

# Volatilite grafiği
plt.figure(figsize=(12,6))
plt.plot(vol_forecast.index, vol_forecast["GARCH_Volatilite"], label="GARCH Volatilite")
plt.plot(vol_forecast.index, vol_forecast["EGARCH_Volatilite"], label="EGARCH Volatilite")
plt.title("ASELS – GARCH ve EGARCH Volatilite Tahminleri (standart sapma)")
plt.legend()
plt.grid()
plt.show()

print("\nTahminler CSV olarak kaydedildi: tahminler_ARIMA_Prophet_GARCH.csv")
