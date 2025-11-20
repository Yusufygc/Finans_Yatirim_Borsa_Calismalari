import yfinance as yf
import pandas as pd

# --- Ayarlar ---
Hisse_Sembolu = 'ASELS.IS'  # ASELSAN'ın Yahoo Finance'taki BIST sembolü
# -----------------

print(f"--- {Hisse_Sembolu} Temel Finansal Rasyolar Çekiliyor (Yahoo Finance) ---")

try:
    # 1. Ticker (Hisse) objesini oluşturma
    aselsan = yf.Ticker(Hisse_Sembolu)

    # 2. Rasyoları içeren ana bilgi sözlüğünü (dictionary) çekme
    bilgiler = aselsan.info

    # 3. İstenen Rasyoları Çekme ve Hesaplama

    # F/K (Fiyat/Kazanç Oranı)
    # yfinance'ta iki farklı F/K değeri olabilir: trailingPE (son 12 ay) veya forwardPE (tahmini)
    fk_orani = bilgiler.get('trailingPE', 'Veri Yok')

    # PD/DD (Piyasa Değeri/Defter Değeri Oranı)
    pddd_orani = bilgiler.get('priceToBook', 'Veri Yok')

    # Temettü Verimi (Dividend Yield)
    # Regular Market için temettü verimi
    temettu_verimi = bilgiler.get('dividendYield') 
    
    if temettu_verimi is not None and temettu_verimi != 'Veri Yok':
         temettu_verimi = f"{(temettu_verimi * 100):.2f}%"
    else:
        temettu_verimi = "Veri Yok"


    # Net Kâr Marjı (Net Profit Margin)
    # yfinance'tan direkt net kâr marjı rasyosu gelmez, ancak brüt kar marjı (grossMargins) kullanılabilir.
    # Net kâr marjını hesaplamak için revenue (gelir) ve netIncome (net kar) gerekir:
    net_gelir = bilgiler.get('netIncomeToCommon', 'Veri Yok')
    toplam_gelir = bilgiler.get('totalRevenue', 'Veri Yok')
    
    net_kar_marji = 'Hesaplanamadı (Veri Yok)'
    if isinstance(net_gelir, (int, float)) and isinstance(toplam_gelir, (int, float)) and toplam_gelir != 0:
        net_kar_marji = f"{(net_gelir / toplam_gelir * 100):.2f}%"

    
    # 4. Sonuçları Tablo Halinde Gösterme
    
    sonuclar = {
        'Rasyo Adı': ['Fiyat/Kazanç (F/K)', 'PD/DD', 'Net Kâr Marjı', 'Temettü Verimi'],
        'Değer': [fk_orani, pddd_orani, net_kar_marji, temettu_verimi]
    }

    df_sonuclar = pd.DataFrame(sonuclar)

    print("\n--- ASELSAN Güncel Temel Rasyoları ---")
    print(df_sonuclar.to_markdown(index=False))
    
    # Not: Yahoo Finance verileri anlık değil, son raporlama dönemine aittir.
    print(f"\n[BİLGİ] Veriler, Yahoo Finance'ın son finansal raporlama dönemine ait temel verileridir.")

except Exception as e:
    print(f"Veri çekme sırasında bir hata oluştu: {e}")
    print("Sembolün ('ASELS.IS') doğru olduğundan ve internet bağlantınızın olduğundan emin olun.")