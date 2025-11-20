import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from pmdarima import auto_arima
from prophet import Prophet
from arch import arch_model

# ============================================
# 1) VERİYİ YÜKLE & HAZIRLA
# ============================================
real =pd.read_csv("D:\\1KodCalismalari\\Projeler\\Finans_Yatirim_Borsa_Calismalari\\DatasetOlusturma\\Dataset\\ASELS.csv")
real["Tarih"] = pd.to_datetime(real["Tarih"], dayfirst=True)
real.set_index("Tarih", inplace=True)

df_prices = real[["Kapanış"]].copy()
df_prices = df_prices.asfreq("B")               # iş günü frekansı
df_prices["Kapanış"] = df_prices["Kapanış"].interpolate()

df_prices["log_close"] = np.log(df_prices["Kapanış"])
df_prices["log_return"] = df_prices["log_close"].diff()
returns = df_prices["log_return"].dropna() * 100

N_FUTURE = 30   # 30 günlük ileri tahmin


# ============================================
# 2) AUTO-ARIMA TAHMİNİ
# ============================================
def run_auto_arima(series, n_future=30):
    model = auto_arima(series, seasonal=False, trace=False,
                       error_action="ignore", suppress_warnings=True)

    pred_log = model.predict(n_periods=n_future)
    future_idx = pd.date_range(series.index[-1] + pd.Timedelta(days=1),
                               periods=n_future, freq="B")

    pred_price = np.exp(pred_log)

    return pd.DataFrame({"ARIMA_Tahmin": pred_price}, index=future_idx)


# ============================================
# 3) PROPHET TAHMİNİ
# ============================================
def run_prophet(df_prices, n_future=30):
    df_p = df_prices.reset_index().rename(columns={"Tarih": "ds", "Kapanış": "y"})

    m = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False
    )
    m.fit(df_p)

    future = m.make_future_dataframe(periods=n_future, freq="B")
    forecast = m.predict(future)

    fc = forecast[forecast["ds"] > df_p["ds"].max()]
    fc = fc.set_index("ds")[["yhat", "yhat_lower", "yhat_upper"]]

    fc.columns = ["Prophet_Tahmin", "Prophet_AltBand", "Prophet_UstBand"]
    return fc


# ============================================
# 4) GARCH + EGARCH VOLATILITE TAHMİNİ
# ============================================
def run_garch_models(returns, n_future=30):

    # GARCH tahmini (analitik)
    garch = arch_model(returns, vol="GARCH", p=1, q=1, mean="Zero", dist="normal")
    garch_fit = garch.fit(disp="off")
    garch_forecast = garch_fit.forecast(horizon=n_future)
    garch_var = garch_forecast.variance.iloc[-1].values
    garch_vol = np.sqrt(garch_var)

    # EGARCH tahmini (iteratif multi-step forecast)
    egarch = arch_model(returns, vol="EGARCH", p=1, q=1, mean="Zero", dist="normal")
    egarch_fit = egarch.fit(disp="off")
    params = egarch_fit.params

    omega = params["omega"]
    alpha = params["alpha[1]"]
    beta  = params["beta[1]"]
    gamma = params.get("gamma[1]", 0)

    last_sigma2 = egarch_fit.conditional_volatility.iloc[-1] ** 2
    prev_log_sigma2 = np.log(last_sigma2)

    egarch_var = []
    for _ in range(n_future):
        expected_abs_z = np.sqrt(2/np.pi)
        expected_z = 0
        new_log = omega + alpha * expected_abs_z + gamma * expected_z + beta * prev_log_sigma2
        prev_log_sigma2 = new_log
        egarch_var.append(np.exp(new_log))

    egarch_vol = np.sqrt(egarch_var)

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


# ============================================
# 5) TÜM TAHMİNLERİ BİRLEŞTİR
# ============================================
arima_fc = run_auto_arima(df_prices["log_close"], N_FUTURE)
prophet_fc = run_prophet(df_prices[["Kapanış"]], N_FUTURE)
vol_fc = run_garch_models(returns, N_FUTURE)

df_fc = arima_fc.join(prophet_fc).join(vol_fc)


# ============================================
# 6) SİNYAL MOTORU
# ============================================
def generate_signals(df, last_real_price):
    signals = []
    current_price = last_real_price   # ilk gün için gerçek kapanış

    for idx, row in df.iterrows():

        prophet = row["Prophet_Tahmin"]
        lower = row["Prophet_AltBand"]
        upper = row["Prophet_UstBand"]
        arima = row["ARIMA_Tahmin"]
        vol = (row["GARCH_Volatilite"] + row["EGARCH_Volatilite"]) / 2

        trend = prophet - current_price
        uncertainty = upper - lower

        if trend > 0 and uncertainty < current_price * 0.01 and vol < 2.5:
            signal = "AL"
        elif trend < 0 or vol > 3.5 or lower < current_price * 0.98:
            signal = "SAT"
        else:
            signal = "TUT"

        signals.append(signal)
        current_price = arima   # bir sonraki gün için referans

    df["Sinyal"] = signals
    return df


# ============================================
# 7) SON GERÇEK KAPANIŞI AL
# ============================================
last_real_price = df_prices["Kapanış"].iloc[-1]

# ============================================
# 8) SİNYALLERİ ÜRET
# ============================================
df_fc = generate_signals(df_fc, last_real_price)


# ============================================
# 9) KAYDET VE YAZDIR
# ============================================
df_fc.to_csv("sinyaller_full_model.csv", encoding="utf-8-sig")

print("\n--- Üretilen Sinyaller ---")
print(df_fc)
