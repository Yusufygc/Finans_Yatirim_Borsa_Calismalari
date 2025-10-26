import yfinance as yf
import pandas as pd
import os
import time
from datetime import datetime, timedelta
from tqdm import tqdm

# --- 1. Ayarlar ---
INPUT_FILE = "Veriler/KAP_Tum_Sirket_Kodlari.csv"  # Hisse kodlarının bulunduğu dosya
OUTPUT_DIR = "DatasetOlusturma/Dataset"            # Verilerin kaydedileceği klasör
LOG_DIR = "DatasetOlusturma"                       # Log dosyalarının tutulacağı klasör
YEARS = 10                                         # Kaç yıllık veri çekileceği
SLEEP_BETWEEN = 1.5                                # İstekler arasında bekleme (saniye)

# --- 2. Klasörleri oluştur ---
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# --- 3. Hisse sembollerini oku ---
try:
    df_symbols = pd.read_csv(INPUT_FILE)
    symbols = df_symbols.iloc[:, 0].dropna().astype(str).tolist()
    print(f"✅ {len(symbols)} adet hisse kodu okundu.")
except FileNotFoundError:
    print(f"❌ Hata: '{INPUT_FILE}' dosyası bulunamadı.")
    exit()

# --- 4. Tarih aralığı ---
end_date = datetime.today()
start_date = end_date - timedelta(days=365 * YEARS)

# --- 5. Log listeleri ---
success_list = []
error_list = []

# --- 6. Veri çekme döngüsü ---
for code in tqdm(symbols, desc="Hisseler işleniyor"):
    symbol = code.strip().upper()
    if not symbol.endswith(".IS"):
        symbol += ".IS"

    output_path = os.path.join(OUTPUT_DIR, f"{symbol.replace('.IS', '')}.csv")

    # Dosya zaten varsa atla
    if os.path.exists(output_path):
        continue

    try:
        # 10 yıllık veri çek
        data = yf.download(symbol, start=start_date, end=end_date, auto_adjust=False, progress=False)

        # Veri boşsa, tüm dönem için tekrar dene
        if data is None or data.empty:
            print(f"⚠️ {symbol} için 10 yıllık veri yok, tüm dönem deneniyor...")
            data = yf.download(symbol, period="max", auto_adjust=False, progress=False)

        # Hâlâ boşsa hata listesine ekle
        if data is None or data.empty:
            print(f"❌ Veri bulunamadı: {symbol}")
            error_list.append(symbol)
            continue

        # MultiIndex kolonları düzleştir
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        # Tarihi kolona çevir
        data.reset_index(inplace=True)

        # Türkçe kolon isimleri
        data.rename(columns={
            "Date": "Tarih",
            "Open": "Açılış",
            "High": "Yüksek",
            "Low": "Düşük",
            "Close": "Kapanış",
            "Adj Close": "Düzeltilmiş_Kapanış",
            "Volume": "Hacim"
        }, inplace=True)

        # Sütun sırası (var olanları koruyarak)
        desired_cols = ["Tarih", "Açılış", "Yüksek", "Düşük", "Kapanış", "Düzeltilmiş_Kapanış", "Hacim"]
        data = data[[c for c in desired_cols if c in data.columns]]

        # CSV kaydet
        data.to_csv(output_path, index=False, encoding="utf-8-sig")

        print(f"✅ {symbol} verisi ({len(data)} satır) kaydedildi.")
        success_list.append(symbol)
        time.sleep(SLEEP_BETWEEN)

    except Exception as e:
        print(f"❌ Hata ({symbol}): {e}")
        error_list.append(symbol)
        continue

# --- 7. Logları kaydet ---
success_df = pd.DataFrame(success_list, columns=["Başarılı_Hisseler"])
error_df = pd.DataFrame(error_list, columns=["Hatalı_Hisseler"])

success_log = os.path.join(LOG_DIR, "Basarili_Hisseler.csv")
error_log = os.path.join(LOG_DIR, "Hatali_Hisseler.csv")

success_df.to_csv(success_log, index=False, encoding="utf-8-sig")
error_df.to_csv(error_log, index=False, encoding="utf-8-sig")

print("\n🎯 Tüm işlemler tamamlandı!")
print(f"📈 Başarılı hisseler: {len(success_list)} adet")
print(f"⚠️ Hatalı hisseler: {len(error_list)} adet")
print(f"✅ Log dosyaları kaydedildi:\n  - {success_log}\n  - {error_log}")
