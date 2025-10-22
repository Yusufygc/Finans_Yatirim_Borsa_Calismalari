import requests
import pandas as pd
from datetime import datetime
import time

# --- 1. API Bilgisi ---
# BURAYA KENDİ FİNNHUB API ANAHTARINIZI GİRİN
API_KEY = ""
# Borsa kodu ABD borsaları için "US" olarak güncellendi
EXCHANGE = "US"

# --- 2. Hisse sembollerini Finnhub'tan al ---
def get_us_symbols():
    """ABD borsalarındaki hisse senedi sembollerini alır."""
    url = f"https://finnhub.io/api/v1/stock/symbol?exchange={EXCHANGE}&token={API_KEY}"
    r = requests.get(url)
    r.raise_for_status()  # Hata durumunda programı durdurur
    symbols = r.json()
    # ABD sembolleri için ".IS" uzantısı gerekmediğinden filtre kaldırıldı.
    return [s["symbol"] for s in symbols]

# --- 3. Hisse verisini Finnhub'tan al ---
def get_quote(symbol):
    """Belirtilen sembol için anlık fiyat verisini çeker."""
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={API_KEY}"
    r = requests.get(url)
    r.raise_for_status()
    data = r.json()
    return data

# --- 4. Filtreleme fonksiyonu ---
def filter_us_stocks(low=4, high=10):
    """ABD hisselerini belirtilen yüzde aralığına göre filtreler."""
    symbols = get_us_symbols()
    print(f"{len(symbols)} adet hisse senedi bulundu. Veriler çekiliyor...")

    results = []
    # Çok fazla sembol olduğu için süreci hızlandırmak ve hataları azaltmak adına
    # genellikle borsa dışı varlıkları belirten sembolleri atlıyoruz.
    filtered_symbols = [s for s in symbols if '.' not in s and '-' not in s]
    print(f"Filtreleme sonrası {len(filtered_symbols)} adet sembol işlenecek...")


    for i, symbol in enumerate(filtered_symbols):
        try:
            data = get_quote(symbol)
            # 'pc' (previous close) değeri 0 ise veya veri boşsa atla
            if not data or "pc" not in data or data["pc"] == 0:
                continue

            prev_close = data["pc"]
            last_price = data["c"]
            change_pct = ((last_price - prev_close) / prev_close) * 100

            if low <= change_pct <= high:
                results.append({
                    "Hisse": symbol,
                    "Önceki Kapanış": round(prev_close, 2),
                    "Son Fiyat": round(last_price, 2),
                    "Değişim (%)": round(change_pct, 2)
                })
        except Exception as e:
            # Hata alınan sembolleri ve hatayı yazdır ama devam et
            print(f"Hata ({symbol}): {e}")

        # API limitlerine takılmamak için her istek arasında kısa bir bekleme yapılır.
        time.sleep(0.3) # Ücretsiz planlar için bekleme süresini biraz artırmak daha güvenli olabilir.

    return pd.DataFrame(results)

# --- 5. Ana program ---
def main():
    # Günlük %4 ile %10 arası artan hisseleri filtrele
    df = filter_us_stocks(4, 10)

    if df.empty:
        print("\nBugün %4 - %10 arası artan bir hisse senedi bulunamadı.")
    else:
        # Sonuçları Değişim (%) sütununa göre büyükten küçüğe sırala
        df = df.sort_values("Değişim (%)", ascending=False)
        print("\n📈 %4 - %10 arası artan hisseler:")
        print(df.to_string()) # DataFrame'in tamamını göstermek için .to_string()

        # Sonuçları CSV dosyasına kaydet
        output_filename = "us_stock_gainers.csv"
        df.to_csv(output_filename, index=False, encoding="utf-8-sig")
        print(f"\nSonuçlar '{output_filename}' dosyasına kaydedildi ✅")

if __name__ == "__main__":
    main()