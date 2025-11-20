import investpy
import pandas as pd

# --- Ayarlar ---
Hisse_Sembolu = 'AAPL'
Ulke_Adi = 'United States'
Baslangic_Tarihi = '01/01/2023'  # Gün/Ay/Yıl formatında
Bitis_Tarihi = '01/01/2024'    # Gün/Ay/Yıl formatında
# -----------------

try:
    # investpy'nin ana fonksiyonunu kullanarak tarihsel veriyi çekme
    veri_seti = investpy.get_stock_historical_data(
        stock=Hisse_Sembolu,
        country=Ulke_Adi,
        from_date=Baslangic_Tarihi,
        to_date=Bitis_Tarihi
    )

    print(f"--- {Ulke_Adi} ({Hisse_Sembolu}) Hissesi Tarihsel Verileri ---")
    
    # Pandas DataFrame'in ilk 5 satırını (başlangıç verilerini) gösterme
    print(veri_seti.head())

    print("\n--- Veri Seti Özeti ---")
    # Veri setinin kaç günlük veri içerdiğini gösterme
    print(f"Toplam gün sayısı: {len(veri_seti)}")
    
    # Kapanış fiyatlarının ortalamasını gösterme
    ortalama_kapanis = veri_seti['Close'].mean()
    print(f"Ortalama Kapanış Fiyatı: ${ortalama_kapanis:.2f}")

except Exception as e:
    print(f"Hata oluştu: {e}")
    print("Sembol, ülke adı veya tarih formatını kontrol edin.")

"""import investpy
import pandas as pd

# --- Ayarlar ---
Hisse_Sembolu = 'ASELS'      # Borsa İstanbul'daki hisse sembolü
Ulke_Adi = 'Turkey'         # Ülke adını 'Turkey' olarak belirtiyoruz
Baslangic_Tarihi = '01/01/2024'  # Gün/Ay/Yıl formatında
Bitis_Tarihi = '27/10/2025'    # Bugünün tarihi (örnek olarak)
# -----------------

print(f"Borsa İstanbul'dan {Hisse_Sembolu} verisi çekiliyor...")

try:
    # investpy ile tarihsel veriyi çekme
    aselsan_veri = investpy.get_stock_historical_data(
        stock=Hisse_Sembolu,
        country=Ulke_Adi,
        from_date=Baslangic_Tarihi,
        to_date=Bitis_Tarihi
    )

    print(f"\n--- ASELSAN ({Hisse_Sembolu}) Hissesi Son Verileri ---")
    # Veri setinin son 5 satırını gösterme (En güncel veriler)
    print(aselsan_veri.tail())

    print("\n--- Veri Seti Özeti ---")
    
    # Kapanış fiyatlarının ortalaması
    ortalama_kapanis = aselsan_veri['Close'].mean()
    print(f"Ortalama Kapanış Fiyatı: ₺{ortalama_kapanis:.2f}")
    
    # En yüksek işlem hacmi olan gün
    en_yuksek_hacim = aselsan_veri['Volume'].max()
    print(f"En Yüksek Hacim: {en_yuksek_hacim:,}")

except Exception as e:
    print(f"Hata oluştu. ASELSAN verisi çekilemedi: {e}")
    print("investpy, Investing.com'dan veri çeker. Sembolün doğruluğunu ve internet bağlantınızı kontrol edin.")
    """