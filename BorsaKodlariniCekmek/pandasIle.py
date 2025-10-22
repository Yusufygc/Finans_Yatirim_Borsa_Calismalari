"""import pandas as pd
import requests

def bist_kodlarini_webden_indir():
   
    #Kendini tarayıcı olarak tanıtarak ve doğru sütun adını ('Hisse', 'Kod', vb.)
    #akıllıca arayarak BIST hisse listesini tek seferde indirir ve CSV olarak kaydeder.
   
    url = "https://www.isyatirim.com.tr/tr-tr/analiz/hisse/Sayfalar/default.aspx"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    print(f"BIST hisse listesi '{url}' adresinden indiriliyor...")

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        tables = pd.read_html(response.text)
        
        print(f"Adresten {len(tables)} adet tablo bulundu. Hisse tablosu analiz ediliyor...")

        hisse_tablosu = None
        # Olası tüm sütun adlarını küçük harfle bir listede topluyoruz
        olasi_sutun_adlari = ['hisse', 'kod', 'sembol']

        for i, table in enumerate(tables):
            print(f"  - Tablo #{i+1} Sütunları: {table.columns.tolist()}")

            # Tablonun sütunları arasında bizim aradığımız isimlerden biri var mı diye kontrol et
            for col in table.columns:
                # Sütun adını temizle (boşlukları sil, küçük harfe çevir)
                temiz_sutun_adi = str(col).strip().lower()
                
                if temiz_sutun_adi in olasi_sutun_adlari:
                    print(f"Doğru sütun bulundu: '{col}'")
                    # Sadece ilgili sütunu al
                    hisse_tablosu = table[[col]].copy()
                    # Sütun adını standart hale getirerek karışıklığı önle
                    hisse_tablosu.columns = ['Kod']
                    break  # İç döngüden çık
            
            if hisse_tablosu is not None:
                break # Dış döngüden çık, çünkü tabloyu bulduk

        if hisse_tablosu is not None and not hisse_tablosu.empty:
            print(f"\nHisse tablosu başarıyla bulundu! Toplam {len(hisse_tablosu)} şirket kodu alınıyor.")
            
            hisse_tablosu['Kod'] = hisse_tablosu['Kod'].str.strip()
            hisse_tablosu.dropna(subset=['Kod'], inplace=True)

            cikti_dosyasi = "bist_symbols.csv"
            hisse_tablosu.to_csv(cikti_dosyasi, index=False, encoding='utf-8-sig')
            
            print("\nİşlem tamamlandı! ✅")
            print(f"Tüm BIST hisse kodları '{cikti_dosyasi}' dosyasına kaydedildi.")
        else:
            print("\nHATA: Sayfadaki tablolarda 'Hisse', 'Kod' veya 'Sembol' adında bir sütun bulunamadı.")
            print("Web sitesinin yapısı değişmiş olabilir. Lütfen yukarıdaki sütun listelerini kontrol edin.")

    except requests.exceptions.RequestException as e:
        print(f"\nHATA: Web sayfasına erişilirken bir sorun oluştu: {e}")
    except Exception as e:
        print(f"\nBEKLENMEDİK HATA: Veri işlenirken bir sorun oluştu: {e}")


if __name__ == "__main__":
    bist_kodlarini_webden_indir()
"""
import pandas as pd
import requests

def bist_kodlarini_kaptan_indir():
    """
    Doğrudan KAP'tan (en resmi kaynak) BIST'te işlem gören tüm şirketlerin
    listesini indirir ve CSV olarak kaydeder.
    """
    # KAP'ın şirketler listesini içeren sayfasının URL'si
    url = "https://www.kap.org.tr/tr/bist-sirketler"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    print(f"En güncel ve eksiksiz BIST hisse listesi KAP'tan indiriliyor...")
    print(f"URL: {url}")

    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        
        tables = pd.read_html(response.text)
        
        if not tables:
            print("HATA: Sayfada hiçbir tablo bulunamadı.")
            return

        # KAP'taki tablo genellikle ilk tablodur.
        hisse_tablosu = tables[0]
        print(f"Tablo bulundu. Sütunlar: {hisse_tablosu.columns.tolist()}")

        # KAP tablosunda hisse kodları "BIST Kodu" sütunundadır.
        if 'BIST Kodu' in hisse_tablosu.columns:
            kod_sutunu = hisse_tablosu[['BIST Kodu']].copy()
            kod_sutunu.columns = ['Kod'] # Sütun adını standartlaştırıyoruz
            
            kod_sutunu.dropna(subset=['Kod'], inplace=True)
            # '-' gibi borsa kodu olmayan değerleri temizle
            kod_sutunu = kod_sutunu[kod_sutunu['Kod'] != '-']
            
            print(f"Toplam {len(kod_sutunu)} adet şirket kodu bulundu.")

            cikti_dosyasi = "bist_symbols_KAP.csv"
            kod_sutunu.to_csv(cikti_dosyasi, index=False, encoding='utf-8-sig')

            print("\nİşlem tamamlandı! ✅")
            print(f"Tüm BIST hisse kodları '{cikti_dosyasi}' dosyasına kaydedildi.")
        else:
            print("HATA: Tabloda 'BIST Kodu' sütunu bulunamadı. KAP sitesinin yapısı değişmiş olabilir.")

    except Exception as e:
        print(f"\nHATA: KAP'tan veri çekilirken bir sorun oluştu: {e}")


if __name__ == "__main__":
    bist_kodlarini_kaptan_indir()