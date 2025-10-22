import pandas as pd
from googlesearch import search
import time
import re
from tqdm import tqdm
import random
import os

# --- AYARLAR ---
# Lütfen bu ayarları kendi dosyanıza göre güncelleyin
girdi_dosyasi = "BorsaKodlariniCekmek/sirketler_isim.csv"
cikti_dosyasi = "BorsaKodlariniCekmek/sirketler_kodlu.csv"
sirket_adi_kolonu = "İsim"  # Şirket adlarının bulunduğu sütunun başlığı
# --- DAHA DA GELİŞTİRİLMİŞ ÖZELLİKLER ---

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
]

def borsa_kodu_bul_son_versiyon(sirket_adi):
    """
    429 Hatalarına karşı maksimum dayanıklılık gösteren, çok yavaş ve sabırlı arama fonksiyonu.
    """
    query = f'"{sirket_adi}" borsa kodu BIST investing'
    max_retries = 3
    # Hata durumunda bekleme süresini önemli ölçüde artırdık
    wait_time = 300  # İlk bekleme süresi: 300 saniye (5 dakika)

    for attempt in range(max_retries):
        try:
            user_agent = random.choice(USER_AGENTS)
            # Normal istekler arasındaki bekleme süresini de artırdık
            pause_duration = random.uniform(10, 25) # 10 ila 25 saniye arasında rastgele bekle
            
            search_results = list(search(query, tld='com', lang='tr', num=5, stop=5, pause=pause_duration, user_agent=user_agent))
            
            guvenilir_siteler = ['investing.com', 'kap.org.tr', 'bigpara.hurriyet.com.tr', 'isyatirim.com.tr']
            
            for url in search_results:
                potential_codes = re.findall(r'\b([A-Z]{4,5})\b', url.upper())
                for code in potential_codes:
                    if code not in ['BIST', 'BORSA', 'HTTPS', 'HTML', 'INDEX', 'FROM']:
                        if any(site in url for site in guvenilir_siteler):
                            return code
            
            for url in search_results:
                potential_codes = re.findall(r'\b([A-Z]{4,5})\b', url.upper())
                for code in potential_codes:
                    if code not in ['BIST', 'BORSA', 'HTTPS', 'HTML', 'INDEX', 'FROM']:
                        return code

            return "Bulunamadı"

        except Exception as e:
            if "429" in str(e):
                print(f"\nUYARI: '{sirket_adi}' için 429 hatası alındı. {wait_time} saniye bekleniyor...")
                time.sleep(wait_time)
                wait_time *= 2
            else:
                print(f"Arama sırasında beklenmedik hata ({sirket_adi}): {e}")
                return "Hata"
    
    print(f"\nKRİTİK: '{sirket_adi}' için tüm denemeler engellendi. Bu hisseyi şimdilik atlıyoruz.")
    return "Engellendi"


def main():
    """
    Ana program: CSV'yi okur, eksik kodları bulur ve dosyayı güncelleyerek kaydeder.
    """
    try:
        if os.path.exists(cikti_dosyasi):
            print(f"'{cikti_dosyasi}' bulundu, kaldığı yerden devam ediliyor...")
            df = pd.read_csv(cikti_dosyasi)
        else:
            print(f"'{girdi_dosyasi}' okunuyor...")
            df = pd.read_csv(girdi_dosyasi)
            df['Borsa Kodu'] = None
    except FileNotFoundError:
        print(f"HATA: '{girdi_dosyasi}' bulunamadı.")
        return

    # NaN, None veya boş string olanları bulmak için daha kapsamlı kontrol
    islem_yapilacak_df = df[df['Borsa Kodu'].isnull() | (df['Borsa Kodu'] == '')].copy()

    if islem_yapilacak_df.empty:
        print("Tüm şirketlerin borsa kodları zaten bulunmuş. İşlem tamamlandı. ✅")
        return

    print(f"Toplam {len(df)} şirketten {len(islem_yapilacak_df)} tanesinin kodu aranacak...")
    
    tqdm.pandas(desc="Borsa Kodları Aranıyor")
    
    islem_yapilacak_df['Borsa Kodu'] = islem_yapilacak_df[sirket_adi_kolonu].progress_apply(borsa_kodu_bul_son_versiyon)

    df.update(islem_yapilacak_df)
    
    df.to_csv(cikti_dosyasi, index=False, encoding='utf-8-sig')

    print("\nİşlem tamamlandı! ✅")
    print(f"Sonuçlar '{cikti_dosyasi}' dosyasına kaydedildi.")
    
    bulunamayanlar = df[df['Borsa Kodu'] == 'Bulunamadı'].shape[0]
    engellenenler = df[df['Borsa Kodu'] == 'Engellendi'].shape[0]
    tamamlananlar = df['Borsa Kodu'].count() - bulunamayanlar - engellenenler
    
    print(f"\nToplam {len(df)} şirketten;")
    print(f"  - {tamamlananlar} tanesinin borsa kodu başarıyla bulundu.")
    print(f"  - {bulunamayanlar} tanesi aramalara rağmen bulunamadı.")
    print(f"  - {engellenenler} tanesi için arama denemeleri Google tarafından engellendi.")


if __name__ == "__main__":
    main()