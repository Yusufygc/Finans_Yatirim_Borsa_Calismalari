#Created by Claude Sonnet 4.5
import yfinance as yf
import pandas as pd
import time
from tqdm import tqdm  # İlerleme çubuğu için

# --- 1. BIST hisse sembollerini dosyadan oku ---
def get_bist_symbols_from_csv(filename="Veriler/KAP_Tum_Sirket_Kodlari.csv"):
    """CSV dosyasından BIST hisse sembollerini okur."""
    try:
        df = pd.read_csv(filename)
        # CSV'deki ilk sütunun sembolleri içerdiğini varsayıyoruz
        # Sütun adını kendi dosyanıza göre güncelleyebilirsiniz, örn: "Symbol" veya "Kod"
        symbols = df.iloc[:, 0].tolist()
        print(f"'{filename}' dosyasından {len(symbols)} adet hisse sembolü okundu.")
        return symbols
    except FileNotFoundError:
        print(f"HATA: '{filename}' dosyası bulunamadı.")
        print("Lütfen BIST hisse sembollerini içeren bir CSV dosyası oluşturun.")
        return None

# --- 2. Bulunamayan hisseleri kaydetme fonksiyonu ---
def save_missing_stocks(missing_stocks, filename="Veriler/bulunmayan_hisseler.csv"):
    """Yahoo Finance'ta bulunamayan hisseleri CSV dosyasına kaydeder."""
    if missing_stocks:
        df_missing = pd.DataFrame(missing_stocks, columns=["Hisse Kodu"])
        df_missing.to_csv(filename, index=False, encoding="utf-8-sig")
        print(f"\n⚠️  {len(missing_stocks)} adet hisse Yahoo Finance'ta bulunamadı.")
        print(f"Bulunamayan hisseler '{filename}' dosyasına kaydedildi.")
    else:
        print("\n✅ Tüm hisseler Yahoo Finance'ta bulundu.")

# --- 3. Filtreleme ve veri çekme fonksiyonu ---
def filter_bist_stocks(low=4, high=10):
    """BIST hisselerini yfinance kullanarak çeker ve filtreler."""
    symbols = get_bist_symbols_from_csv()
    if symbols is None:
        return pd.DataFrame(), []  # Boş DataFrame ve liste döndür
    
    print("Hisse verileri çekiliyor ve filtreleniyor...")
    results = []
    missing_stocks = []  # Bulunamayan hisseleri tutacak liste
    
    # tqdm ile ilerleme çubuğu oluşturarak süreci takip et
    for symbol in tqdm(symbols, desc="Hisseler taranıyor"):
        try:
            # yfinance için BIST sembollerinin sonuna ".IS" eklenmelidir
            ticker_symbol = f"{symbol}.IS"
            
            # Ticker nesnesini oluştur
            hisse = yf.Ticker(ticker_symbol)
            
            # .info, hisse hakkında anlık ve temel bilgileri içeren bir sözlüktür
            info = hisse.info
            
            # Eğer info boş veya sadece temel bilgiler varsa, hisse bulunamadı demektir
            # Yahoo Finance bulamadığında genellikle çok az bilgi döner
            if not info or len(info) < 5 or 'previousClose' not in info:
                missing_stocks.append(symbol)
                continue
            
            # Gerekli verilerin varlığını kontrol et
            prev_close = info.get('previousClose')
            # Bazen 'currentPrice' yerine 'regularMarketPrice' dolu olabilir
            last_price = info.get('currentPrice', info.get('regularMarketPrice')) 
            
            # Veriler eksikse veya sıfırsa bu hisseyi atla
            if not prev_close or not last_price or prev_close == 0:
                missing_stocks.append(symbol)
                continue
            
            # Yüzdelik değişimi hesapla
            change_pct = ((last_price - prev_close) / prev_close) * 100
            
            # Filtreleme koşulunu uygula
            if low <= change_pct <= high:
                results.append({
                    "Hisse": symbol,
                    "Önceki Kapanış": round(prev_close, 2),
                    "Son Fiyat": round(last_price, 2),
                    "Değişim (%)": round(change_pct, 2)
                })
            
            # Yahoo Finance API'sini yormamak ve engellenmemek için çok kısa bir bekleme ekle
            time.sleep(0.3)
            
        except Exception as e:
            # Hata veren hisseleri bulunamayan listesine ekle
            missing_stocks.append(symbol)
            # İsterseniz hatayı görmek için yorum satırını kaldırabilirsiniz:
            # print(f"Hata ({symbol}): {e}")
            continue
    
    return pd.DataFrame(results), missing_stocks

# --- 4. Ana program ---
def main():
    df, missing_stocks = filter_bist_stocks(4, 10)
    
    # Bulunamayan hisseleri kaydet
    save_missing_stocks(missing_stocks)
    
    if df.empty:
        print("\nBugün %4 - %10 arası artan bir BIST hissesi bulunamadı.")
    else:
        df = df.sort_values("Değişim (%)", ascending=False)
        print("\n📈 %4 - %10 arası artan BIST hisseleri:")
        # to_string() ile tüm sonuçları konsolda göster
        print(df.to_string())
        
        output_filename = "Veriler/bist_artanlar_yfinance.csv"
        df.to_csv(output_filename, index=False, encoding="utf-8-sig")
        print(f"\nSonuçlar '{output_filename}' dosyasına kaydedildi ✅")

if __name__ == "__main__":
    main()