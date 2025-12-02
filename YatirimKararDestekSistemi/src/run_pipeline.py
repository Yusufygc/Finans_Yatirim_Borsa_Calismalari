import pandas as pd
import os
import sys

# Mevcut dizini path'e ekleyelim ki modül importlarında sorun çıkmasın
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_loader import DataLoader
from feature_engineering import FeatureEngineer
from model_price_prediction import HybridModel
from risk_profile import RiskManager
from evaluation import ModelEvaluator
from risk_assessment import RiskAssessment  # <--- YENİ: Risk Değerlendirme Modülü

# ==========================================
# AYARLAR
# ==========================================
# Not: Dosya yolunu kendi bilgisayarınızdaki yapıya göre güncel tutun.
DATA_FILE = "D:\\1KodCalismalari\\Projeler\\Finans_Yatirim_Borsa_Calismalari\\YatirimKararDestekSistemi\\data\\raw\\ADEL.csv"  
FORECAST_DAYS = 10  # Gelecek kaç gün tahmin edilsin?

def get_user_risk_profile():
    """
    Kullanıcıya risk profilini nasıl belirlemek istediğini sorar ve profili döndürür.
    """
    print("\n>>> RİSK PROFİLİ BELİRLEME ADIMI <<<")
    print("1. Otomatik Anket ile Belirle (Önerilen)")
    print("2. Manuel Giriş Yap (Hızlı Mod)")
    
    while True:
        choice = input("Seçiminiz (1 veya 2): ").strip()
        
        if choice == '1':
            # OOP Prensibi: RiskAssessment sınıfından bir nesne oluşturup işi ona devrediyoruz.
            assessment = RiskAssessment()
            return assessment.run_assessment()
            
        elif choice == '2':
            print("Mevcut Profiller: 'agresif', 'orta', 'temkinli'")
            profile = input("Profilinizi yazın: ").lower().strip()
            if profile in ["agresif", "orta", "temkinli"]:
                return profile
            print("[HATA] Geçersiz profil ismi! Lütfen tekrar deneyin.")
            
        else:
            print("[HATA] Lütfen 1 veya 2 giriniz.")

def main():
    # Konsol Ayarları (Kompakt Görünüm İçin)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 200)
    pd.set_option('display.max_colwidth', 25) 
    pd.set_option('display.float_format', '{:,.2f}'.format) 

    print("############################################################")
    print("#          YATIRIM KARAR DESTEK SİSTEMİ (EĞİTİM & KAYIT)   #")
    print("############################################################")

    ticker_name = os.path.splitext(os.path.basename(DATA_FILE))[0]

    # ---------------------------------------------------------
    # ADIM 0: RİSK PROFİLİNİ BELİRLE
    # ---------------------------------------------------------
    # Model eğitimi zaman alacağı için önce kullanıcıdan girdiyi alıyoruz.
    user_risk_profile = get_user_risk_profile()
    print(f"[BİLGİ] Analiz '{user_risk_profile.upper()}' risk profiline göre yapılandırılacak.")

    # ---------------------------------------------------------
    # ADIM 1: VERİ YÜKLEME
    # ---------------------------------------------------------
    try:
        loader = DataLoader(DATA_FILE)
        df = loader.load_data()
    except Exception as e:
        print(f"[KRİTİK HATA] Veri yüklenemedi: {e}")
        return

    # ---------------------------------------------------------
    # ADIM 2: ÖZELLİK MÜHENDİSLİĞİ
    # ---------------------------------------------------------
    print("\n[İşlem] Teknik indikatörler hesaplanıyor...")
    fe = FeatureEngineer(df)
    df = fe.add_indicators()
    current_price = df["Kapanış"].iloc[-1]
    
    # ---------------------------------------------------------
    # ADIM 3: BACKTEST
    # ---------------------------------------------------------
    # Modelin geçmiş performansını görmek istemiyorsanız burayı yorum satırı yapabilirsiniz.
    evaluator = ModelEvaluator(df, test_days=30)
    evaluator.evaluate()

    # ---------------------------------------------------------
    # ADIM 4: FİNAL EĞİTİM VE TAHMİN
    # ---------------------------------------------------------
    print(f"\n>>> GELECEK {FORECAST_DAYS} GÜN İÇİN TAHMİN (Hisse: {ticker_name}) <<<")
    
    model_engine = HybridModel(n_future=FORECAST_DAYS)
    # save_models=True ile modelleri 'models/' klasörüne kaydediyoruz
    forecast_results = model_engine.run_hybrid_forecast(df, save_models=True, ticker=ticker_name)

    # ---------------------------------------------------------
    # ADIM 5: SİNYAL ÜRETİMİ (DİNAMİK RİSK YÖNETİMİ)
    # ---------------------------------------------------------
    forecast_results["Tahmin_Ortalama"] = forecast_results["Final_Ensemble"]
    
    # BURASI KRİTİK: Artık manuel 'temkinli' yerine anketten gelen 'user_risk_profile'ı kullanıyoruz.
    advisor = RiskManager(risk_profile=user_risk_profile)
    
    final_table = advisor.generate_signals(
        forecast_results, 
        current_price, 
        current_rsi=df["RSI"].iloc[-1], 
        current_sma=df["SMA_50"].iloc[-1]
    )

    # ---------------------------------------------------------
    # ADIM 6: RAPORLAMA
    # ---------------------------------------------------------
    print("\n[ÖZET TAHMİN TABLOSU]")
    print("-" * 120)
    
    # Gösterilecek sütunlar
    cols = [
        "Tahmin_ARIMA", "Tahmin_Prophet", "TS_Ensemble",
        "Tahmin_SVR", "Tahmin_RandomForest", "Tahmin_LightGBM", "ML_Ensemble",
        "Final_Ensemble", "Sinyal", "Sinyal_Gerekcesi"
    ]
    
    # Ekran çıktısı için kopya alıp sütun isimlerini kısaltıyoruz
    display_df = final_table[cols].copy()
    display_df.rename(columns={
        "Tahmin_ARIMA": "ARIMA",
        "Tahmin_Prophet": "Prophet",
        "TS_Ensemble": "TS_ORT",
        "Tahmin_SVR": "SVR",
        "Tahmin_RandomForest": "R.Forest",
        "Tahmin_LightGBM": "L.GBM",
        "ML_Ensemble": "ML_ORT",
        "Final_Ensemble": "FİNAL",
        "Sinyal": "KARAR",
        "Sinyal_Gerekcesi": "NEDEN"
    }, inplace=True)
    
    print(display_df.to_string())
    print("-" * 120)
    
    # Raporu, belirlenen profil ismini de içerecek şekilde kaydedelim
    report_file = f"{ticker_name}_{user_risk_profile}_final_tahmin_raporu.csv"
    final_table.to_csv(report_file)
    print(f"\n[BİLGİ] Rapor '{report_file}' olarak kaydedildi.")
    print(f"[BİLGİ] Eğitilen modeller 'models/{ticker_name}/' klasörüne kaydedildi.")

if __name__ == "__main__":
    main()