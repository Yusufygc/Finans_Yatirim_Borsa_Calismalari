import yfinance as yf
import pandas as pd
import time
from tqdm import tqdm  # İlerleme çubuğu için

# --- 1. BIST hisse sembollerini dosyadan oku ---
def get_bist_symbols_from_csv(filename="Veriler/KAP_Tum_Sirket_Kodlari2.csv"):
    """CSV dosyasından BIST hisse sembollerini okur."""
    try:
        df = pd.read_csv(filename)
        # CSV'deki ilk sütunun sembolleri içerdiğini varsayıyoruz
        symbols = df.iloc[:, 0].tolist()
        print(f"'{filename}' dosyasından {len(symbols)} adet hisse sembolü okundu.")
        return symbols
    except FileNotFoundError:
        print(f"HATA: '{filename}' dosyası bulunamadı.")
        print("Lütfen BIST hisse sembollerini içeren bir CSV dosyası oluşturun.")
        return None

# --- 2. Bulunamayan hisseleri kaydetme fonksiyonu ---
def save_missing_stocks(missing_stocks, filename="Veriler/bulunmayan_hisseler.csv"):
    if missing_stocks:
        df_missing = pd.DataFrame(missing_stocks, columns=["Hisse Kodu"])
        df_missing.to_csv(filename, index=False, encoding="utf-8-sig")
        print(f"\n⚠️  {len(missing_stocks)} adet hisse Yahoo Finance'ta bulunamadı (Kaydedildi: {filename}).")
    else:
        print("\n✅ Tüm hisseler Yahoo Finance'ta bulundu.")

# --- 3. Kullanıcı Tercihlerini Alma ---
def get_user_preferences():
    print("\n" + "="*40)
    print("   BIST HİSSE FİLTRELEME ARACI")
    print("="*40)
    print("Lütfen filtreleme yöntemini seçiniz:")
    print("1. Yüzdelik Değişime Göre (Örn: %4 ile %10 arası artanlar)")
    print("2. Kapanış Fiyatına Göre (Örn: 2.95 TL ile 3.00 TL arası)")
    
    while True:
        choice = input("Seçiminiz (1 veya 2): ").strip()
        if choice == '1':
            # --- Yüzdelik Filtre ---
            print("\n--- Yüzdelik Değişim Filtresi ---")
            try:
                min_val = float(input("Minimum Yüzde (örn: 4): ").replace(',', '.'))
                max_val = float(input("Maksimum Yüzde (örn: 10): ").replace(',', '.'))
                return {"type": "percent", "min": min_val, "max": max_val}
            except ValueError:
                print("Hata: Lütfen geçerli bir sayı giriniz.")
        
        elif choice == '2':
            # --- Fiyat Filtresi ---
            print("\n--- Kapanış Fiyatı Filtresi ---")
            print("Fiyat filtreleme türünü seçiniz:")
            print("A. Fiyat Aralığı (Örn: 2.95 ile 3.00 TL arası)")
            print("B. Tek Fiyat Sınırı (Örn: 50 TL'den küçükler veya 100 TL'den büyükler)")
            
            sub_choice = input("Seçiminiz (A veya B): ").strip().upper()
            
            try:
                if sub_choice == 'A':
                    min_price = float(input("Minimum Fiyat (TL): ").replace(',', '.'))
                    max_price = float(input("Maksimum Fiyat (TL): ").replace(',', '.'))
                    return {"type": "price_range", "min": min_price, "max": max_price}
                
                elif sub_choice == 'B':
                    print("Operatör seçiniz:")
                    print("1. Büyüktür ( > X TL)")
                    print("2. Küçüktür ( < X TL)")
                    op_choice = input("Seçim (1 veya 2): ").strip()
                    limit_price = float(input("Fiyat Sınırı (TL): ").replace(',', '.'))
                    
                    if op_choice == '1':
                        return {"type": "price_single", "operator": ">", "value": limit_price}
                    else:
                        return {"type": "price_single", "operator": "<", "value": limit_price}
                else:
                    print("Geçersiz seçim, lütfen tekrar deneyin.")
            except ValueError:
                print("Hata: Lütfen geçerli bir sayı giriniz.")
        
        else:
            print("Geçersiz giriş. Lütfen 1 veya 2 yazıp Enter'a basın.")

# --- 4. Filtreleme ve veri çekme fonksiyonu (Güncellendi) ---
def filter_bist_stocks(criteria):
    """Kullanıcı kriterlerine göre hisseleri filtreler."""
    symbols = get_bist_symbols_from_csv()
    if symbols is None:
        return pd.DataFrame(), []
    
    print("\nHisse verileri çekiliyor ve kriterlere göre taranıyor...")
    results = []
    missing_stocks = []
    
    for symbol in tqdm(symbols, desc="Hisseler taranıyor"):
        try:
            ticker_symbol = f"{symbol}.IS"
            hisse = yf.Ticker(ticker_symbol)
            info = hisse.info
            
            # Veri kontrolü
            if not info or 'previousClose' not in info:
                missing_stocks.append(symbol)
                continue
            
            prev_close = info.get('previousClose')
            last_price = info.get('currentPrice', info.get('regularMarketPrice'))
            
            if not prev_close or not last_price:
                missing_stocks.append(symbol)
                continue
            
            # Hesaplamalar
            change_pct = ((last_price - prev_close) / prev_close) * 100
            
            # --- FİLTRELEME MANTIĞI ---
            match = False
            
            if criteria["type"] == "percent":
                if criteria["min"] <= change_pct <= criteria["max"]:
                    match = True
            
            elif criteria["type"] == "price_range":
                if criteria["min"] <= last_price <= criteria["max"]:
                    match = True
            
            elif criteria["type"] == "price_single":
                if criteria["operator"] == ">":
                    if last_price > criteria["value"]:
                        match = True
                elif criteria["operator"] == "<":
                    if last_price < criteria["value"]:
                        match = True

            # Eşleşme varsa listeye ekle
            if match:
                results.append({
                    "Hisse": symbol,
                    "Önceki Kapanış": round(prev_close, 2),
                    "Son Fiyat": round(last_price, 2),
                    "Değişim (%)": round(change_pct, 2)
                })
            
            time.sleep(0.1) # API nezaketi
            
        except Exception:
            missing_stocks.append(symbol)
            continue
    
    return pd.DataFrame(results), missing_stocks

# --- 5. Ana program ---
def main():
    # 1. Kullanıcıdan ne yapmak istediğini öğren
    criteria = get_user_preferences()
    
    print(f"\nSeçilen Kriterler: {criteria}")
    
    # 2. Taramayı başlat
    df, missing_stocks = filter_bist_stocks(criteria)
    
    # 3. Sonuçları işle
    save_missing_stocks(missing_stocks)
    
    if df.empty:
        print("\n❌ Kriterlere uygun hiç hisse bulunamadı.")
    else:
        # Sıralama: Fiyat filtresiyse Fiyata göre, Değişimse Değişime göre sırala
        sort_col = "Son Fiyat" if "price" in criteria["type"] else "Değişim (%)"
        df = df.sort_values(sort_col, ascending=False)
        
        print(f"\n📈 Kriterlere Uyan BIST Hisseleri ({len(df)} adet):")
        print(df.to_string())
        
        output_filename = "Veriler/filtrelenmis_hisseler.csv"
        df.to_csv(output_filename, index=False, encoding="utf-8-sig")
        print(f"\n💾 Sonuçlar '{output_filename}' dosyasına kaydedildi.")

if __name__ == "__main__":
    main()