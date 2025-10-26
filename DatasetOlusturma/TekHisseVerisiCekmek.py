import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# --- 1. Tarih aralığı ---
end_date = datetime.today()
start_date = end_date - timedelta(days=365 * 10)

# --- 2. Hisse verisini çek ---
symbol = "YYAPI.IS"
df = yf.download(symbol, start=start_date, end=end_date, auto_adjust=False)

# --- 3. MultiIndex kolonları düzleştir ---
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

# --- 4. Tarihi index'ten kolona çevir ---
df.reset_index(inplace=True)

# --- 5. Sütun adlarını Türkçeleştir ---
df.rename(columns={
    "Date": "Tarih",
    "Open": "Açılış",
    "High": "Yüksek",
    "Low": "Düşük",
    "Close": "Kapanış",
    "Adj Close": "Düzeltilmiş_Kapanış",
    "Volume": "Hacim"
}, inplace=True)

# --- 6. Sütun sırasını düzenle ---
df = df[["Tarih", "Açılış", "Yüksek", "Düşük", "Kapanış", "Düzeltilmiş_Kapanış", "Hacim"]]

# --- 7. CSV’ye kaydet ---
csv_filename = "DatasetOlusturma/YYAPI_10y_data.csv"
df.to_csv(csv_filename, index=False, encoding="utf-8-sig")

# --- 8. Özet ---
print(df.head())
print(f"\nToplam {len(df)} satır veri çekildi ve '{csv_filename}' dosyasına kaydedildi.")
