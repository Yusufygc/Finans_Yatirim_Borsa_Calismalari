
import pandas as pd
import os
from data_loader import DataLoader
from feature_engineering import FeatureEngineer
from model_price_prediction import HybridModel
from risk_profile import RiskManager
from evaluation import ModelEvaluator
# ==========================================
# AYARLAR
# ==========================================
DATA_FILE = "D:\\1KodCalismalari\\Projeler\\Finans_Yatirim_Borsa_Calismalari\\YatirimKararDestekSistemi\\data\\raw\\ALTNY.csv"  # Dosya yolunu kendinize göre düzenleyin  
FORECAST_DAYS = 10  # Gelecek kaç gün tahmin edilsin?

def main():
    # Konsol Ayarları (Kompakt Görünüm İçin)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 200) # Konsol genişliği
    pd.set_option('display.max_colwidth', 25) # Uzun metinleri (Gerekçe) kırp
    pd.set_option('display.float_format', '{:,.2f}'.format) # Virgülden sonra 2 hane

    print("############################################################")
    print("#          YATIRIM KARAR DESTEK SİSTEMİ (EĞİTİM & KAYIT)   #")
    print("############################################################")

    ticker_name = os.path.splitext(os.path.basename(DATA_FILE))[0]

    # 1. VERİ YÜKLEME
    try:
        loader = DataLoader(DATA_FILE)
        df = loader.load_data()
    except Exception as e:
        print(f"HATA: {e}")
        return

    # 2. ÖZELLİK MÜHENDİSLİĞİ
    fe = FeatureEngineer(df)
    df = fe.add_indicators()
    current_price = df["Kapanış"].iloc[-1]
    
    # 3. BACKTEST
    evaluator = ModelEvaluator(df, test_days=30)
    evaluator.evaluate()

    # 4. FİNAL EĞİTİM VE TAHMİN
    print(f"\n>>> GELECEK {FORECAST_DAYS} GÜN İÇİN TAHMİN (Hisse: {ticker_name}) <<<")
    
    model_engine = HybridModel(n_future=FORECAST_DAYS)
    # save_models=True ile modelleri ana dizindeki 'models/' klasörüne kaydediyoruz
    forecast_results = model_engine.run_hybrid_forecast(df, save_models=True, ticker=ticker_name)

    # 5. SİNYAL ÜRETİMİ
    forecast_results["Tahmin_Ortalama"] = forecast_results["Final_Ensemble"]
    advisor = RiskManager(risk_profile="agresif")  # Profil: agresif, orta, temkinli
    
    final_table = advisor.generate_signals(
        forecast_results, 
        current_price, 
        current_rsi=df["RSI"].iloc[-1], 
        current_sma=df["SMA_50"].iloc[-1]
    )

    # 6. RAPORLAMA (Kompakt Tablo Düzeni)
    print("\n[ÖZET TAHMİN TABLOSU]")
    print("-" * 120)
    
    # Gösterilecek orijinal sütunlar
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
    
    # Tabloyu yazdır
    print(display_df.to_string())
    print("-" * 120)
    
    report_file = f"{ticker_name}_final_tahmin_raporu.csv"
    final_table.to_csv(report_file)
    print(f"\n[BİLGİ] Rapor '{report_file}' olarak kaydedildi.")
    print(f"[BİLGİ] Eğitilen modeller 'models/{ticker_name}/' klasörüne kaydedildi.")

if __name__ == "__main__":
    main()