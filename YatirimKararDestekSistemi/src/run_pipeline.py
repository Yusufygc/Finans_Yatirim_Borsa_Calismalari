
import pandas as pd
from data_loader import DataLoader
from feature_engineering import FeatureEngineer
from model_price_prediction import HybridModel
from risk_profile import RiskManager
from evaluation import ModelEvaluator
# ==========================================
# AYARLAR
# ==========================================
DATA_FILE = "D:\\1KodCalismalari\\Projeler\\Finans_Yatirim_Borsa_Calismalari\\YatirimKararDestekSistemi\\data\\raw\\ASELS.csv"  # Dosya yolunu kendinize göre düzenleyin  
FORECAST_DAYS = 10  # Gelecek kaç gün tahmin edilsin?

def main():
    # Konsol ayarları (Tabloların düzgün görünmesi için)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    pd.set_option('display.float_format', '{:,.2f}'.format)

    print("############################################################")
    print("#          YATIRIM KARAR DESTEK SİSTEMİ (FULL RAPOR)       #")
    print("############################################################")

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
    
    # 3. BACKTEST (DEĞERLENDİRME) AŞAMASI
    evaluator = ModelEvaluator(df, test_days=30)
    evaluator.evaluate()

    # 4. GELECEK TAHMİNİ (FORECAST)
    print(f"\n>>> GELECEK {FORECAST_DAYS} GÜN İÇİN DETAYLI MODEL TAHMİNLERİ <<<")
    
    model_engine = HybridModel(n_future=FORECAST_DAYS)
    forecast_results = model_engine.run_hybrid_forecast(df)

    # 5. RİSK VE SİNYAL ÜRETİMİ
    # Tahmin ortalaması olarak Final Ensemble'ı kullan
    forecast_results["Tahmin_Ortalama"] = forecast_results["Final_Ensemble"]
    
    advisor = RiskManager(risk_profile="orta")
    
    # Sinyal motoruna güncel indikatörleri ver
    final_table = advisor.generate_signals(
        forecast_results, 
        current_price, 
        current_rsi=df["RSI"].iloc[-1], 
        current_sma=df["SMA_50"].iloc[-1]
    )

    # 6. BÜYÜK TABLOYU YAZDIR
    print("\n[DETAYLI SONUÇ TABLOSU]")
    print("-" * 120)
    
    # Gösterilecek sütunlar (Tüm modelleri istediniz)
    cols = [
        "Tahmin_ARIMA", "Tahmin_Prophet", "TS_Ensemble",      # Zaman Serisi Grubu
        "Tahmin_SVR", "Tahmin_RandomForest", "Tahmin_LightGBM", "ML_Ensemble", # ML Grubu
        "Final_Ensemble", # Ağırlıklı Sonuç
        "Sinyal"
    ]
    
    # Tabloyu yazdır
    print(final_table[cols].to_string())
    print("-" * 120)
    
    # Kaydet
    final_table.to_csv("tam_detayli_rapor.csv")
    print("\n[BİLGİ] Tüm veriler 'tam_detayli_rapor.csv' dosyasına da kaydedildi.")

if __name__ == "__main__":
    main()