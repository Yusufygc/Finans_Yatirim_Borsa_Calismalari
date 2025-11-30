
import pandas as pd
from data_loader import DataLoader
from feature_engineering import FeatureEngineer
from model_price_prediction import HybridModel
from risk_profile import RiskManager

# ==========================================
# AYARLAR
# ==========================================
DATA_PATH = "D:\\1KodCalismalari\\Projeler\\Finans_Yatirim_Borsa_Calismalari\\YatirimKararDestekSistemi\\data\\raw\\ASELS.csv"  # Dosya yolunu kendinize göre düzenleyin  
# NOT: Artık tek bir profil seçmiyoruz, kod hepsini karşılaştırmalı gösterecek.

def main():
    print("========================================")
    print("   YATIRIM KARAR DESTEK SİSTEMİ v2.1    ")
    print("   (Detaylı Ensemble & Çoklu Profil)    ")
    print("========================================")

    # 1. ADIM: Veri Yükleme
    loader = DataLoader(DATA_PATH)
    try:
        df = loader.load_data()
    except Exception as e:
        print(f"HATA: {e}")
        return

    # 2. ADIM: Özellik Mühendisliği
    fe = FeatureEngineer(df)
    df_with_indicators = fe.add_indicators()
    
    current_price = df_with_indicators["Kapanış"].iloc[-1]
    current_rsi = df_with_indicators["RSI"].iloc[-1]
    current_sma = df_with_indicators["SMA_50"].iloc[-1]
    
    print(f"[BİLGİ] Piyasa Durumu:")
    print(f"   -> Fiyat: {current_price:.2f} TL")
    print(f"   -> RSI (14): {current_rsi:.2f}")
    print(f"   -> SMA (50): {current_sma:.2f}")

    # 3. ADIM: Model Eğitimi ve Tahmin (10 Günlük)
    model_engine = HybridModel(n_future=10) 
    forecast_results = model_engine.run_hybrid_forecast(df_with_indicators)
    
    # 4. ADIM: Karar Mekanizması (ÇOKLU PROFİL)
    # Tahmin ortalamasını 'Final_Ensemble' olarak ayarlayalım
    forecast_results["Tahmin_Ortalama"] = forecast_results["Final_Ensemble"]
    
    # Her üç profil için de sinyal üretip tabloya ekleyelim
    profiles = ["temkinli", "orta", "agresif"]
    
    for profile in profiles:
        advisor = RiskManager(risk_profile=profile)
        # Sinyalleri geçici bir DataFrame'e alıp ana tabloya sadece 'Sinyal' sütununu ekleyelim
        temp_df = advisor.generate_signals(
            forecast_results.copy(), # Orijinal tabloyu bozmamak için kopya gönderiyoruz
            current_price, 
            current_rsi=current_rsi, 
            current_sma=current_sma
        )
        # Sütun ismini profile göre dinamik yapalım (Örn: Sinyal_Orta, Sinyal_Agresif)
        forecast_results[f"Sinyal_{profile.capitalize()}"] = temp_df["Sinyal"]
        
        # Sadece 'Orta' profilin gerekçesini ana tabloya ekleyelim (Hepsi benzer gerekçeler üretecektir)
        if profile == "orta":
            forecast_results["Gerekce"] = temp_df["Sinyal_Gerekcesi"]

    # 5. ADIM: Sonuçları Göster ve Kaydet
    print("\n" + "="*100)
    print(f"   GELECEK 10 GÜN İÇİN DETAYLI KARŞILAŞTIRMA VE SİNYALLER")
    print("="*100)
    
    # Görmek istediğiniz sütunlar
    cols_to_show = [
        "TS_Ensemble",       # Zaman Serisi (Arima+Prophet)
        "ML_Ensemble",       # Yapay Zeka (SVR+RF+LightGBM)
        "Final_Ensemble",    # Hepsinin Ortalaması
        "Sinyal_Temkinli",   # Farklı profillerin kararları
        "Sinyal_Orta",
        "Sinyal_Agresif",
        "Gerekce"            # Neden bu kararı verdi?
    ]
    
    pd.set_option('display.max_colwidth', 40) # Gerekçe sütunu çok uzamasın
    pd.set_option('display.width', 1000)
    
    # Ekrana yazdır
    print(forecast_results[cols_to_show].head(10).to_string())
    
    # output_file = "data\\result\\yatirim_tavsiyeleri_detayli.csv"
    # forecast_results.to_csv(output_file)
    # print(f"\n[BAŞARILI] Detaylı rapor '{output_file}' dosyasına kaydedildi.")

if __name__ == "__main__":
    main()