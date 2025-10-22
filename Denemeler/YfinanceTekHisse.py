import yfinance as yf

# BIST hisse sembolünü .IS uzantısıyla belirtin
try:
    hisse = yf.Ticker("GARAN.IS")

    # .info sözlüğü hisse hakkında birçok anlık bilgi içerir
    hisse_bilgisi = hisse.info
    
    onceki_kapanis = hisse_bilgisi.get('previousClose')
    son_fiyat = hisse_bilgisi.get('currentPrice', hisse_bilgisi.get('regularMarketPrice')) # Anlık fiyatı al

    if onceki_kapanis and son_fiyat and onceki_kapanis > 0:
        degisim_yuzdesi = ((son_fiyat - onceki_kapanis) / onceki_kapanis) * 100

        print(f"Hisse: GARAN.IS")
        print(f"Önceki Kapanış: {onceki_kapanis:.2f}")
        print(f"Son Fiyat: {son_fiyat:.2f}")
        print(f"Günlük Değişim: %{degisim_yuzdesi:.2f}")
    else:
        print("Fiyat verileri alınamadı. Lütfen sembolü ve internet bağlantınızı kontrol edin.")

except Exception as e:
    print(f"Bir hata oluştu: {e}")