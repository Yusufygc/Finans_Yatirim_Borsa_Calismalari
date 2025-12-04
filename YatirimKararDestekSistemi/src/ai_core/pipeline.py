# src/ai_core/pipeline.py

import pandas as pd
import os
import sys

# Modül yollarını ayarlama
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_core.data_loader import DataLoader
from ai_core.feature_engineering import FeatureEngineer
from ai_core.model_price_prediction import HybridModel
from ai_core.risk_profile import RiskManager
# from ai_core.evaluation import ModelEvaluator
# from ai_core.risk_assessment import RiskAssessment


def run_analysis_for_stock(file_path, risk_profile="orta"):
    """
    Verilen hisse senedi dosyası için uçtan uca AI analizini çalıştırır.
    """
    
    # 1. Dosya Kontrolü
    if not os.path.exists(file_path):
        # Dosya yoksa None döndür, çağıran yer hatayı yönetsin
        print(f"HATA: Veri dosyası bulunamadı -> {file_path}")
        return None

    print(f"\n>>>> Analiz Başlatılıyor: {os.path.basename(file_path)} <<<<")

    # 2. Veri Yükleme
    loader = DataLoader(file_path)
    df = loader.load_data()
    
    # 3. Özellik Mühendisliği
    engineer = FeatureEngineer(df)
    # feature_engineering.py dosyanızda fonksiyon adı 'create_features' ise:
    df_featured = engineer.create_features()
    
    # ---------------------------------------------------------
    # DÜZELTİLEN KISIM BAŞLANGIÇ
    # ---------------------------------------------------------
    # 4. Model Tahmini
    # Hata veren satır: HybridModel(df_featured, forecast_days=10) idi.
    # Doğrusu: Sadece n_future parametresi verilmeli.
    model_engine = HybridModel(n_future=10) 
    
    # Hata veren satır: model_engine.run_all_models() idi.
    # Doğrusu: Fonksiyonun adı run_hybrid_forecast ve df burada verilmeli.
    # Ayrıca ticker ismini dosya adından alıp model kaydı için gönderebiliriz.
    ticker_name = os.path.basename(file_path).replace('.csv', '')
    forecast_df = model_engine.run_hybrid_forecast(df_featured, save_models=True, ticker=ticker_name)
    # ---------------------------------------------------------
    # DÜZELTİLEN KISIM BİTİŞ
    # ---------------------------------------------------------
    
    # 5. Risk Yönetimi ve Sinyal Üretimi
    risk_man = RiskManager(risk_profile=risk_profile)
    
    # Son güncel veriler
    if "Close" in df_featured.columns:
        current_close = df_featured["Close"].iloc[-1]
    elif "Kapanış" in df_featured.columns:
        current_close = df_featured["Kapanış"].iloc[-1]
    else:
        current_close = df_featured.iloc[-1, 0] # İlk sütunu al

    current_rsi = df_featured["RSI"].iloc[-1] if "RSI" in df_featured.columns else 50
    current_sma = df_featured["SMA_50"].iloc[-1] if "SMA_50" in df_featured.columns else current_close
    
    # Sinyalleri oluştur
    final_table = risk_man.generate_signals(
        forecast_df, 
        current_price=current_close,
        current_rsi=current_rsi, 
        current_sma=current_sma
    )
    
    # Yarınki tahmini al (İlk satır)
    next_day_prediction = final_table.iloc[0]
    
    # Sonucu Döndür
    result = {
        "predicted_price": float(next_day_prediction["Final_Ensemble"]),
        "signal": next_day_prediction["Sinyal"],
        "reason": next_day_prediction["Sinyal_Gerekcesi"],
        "volatility": float(next_day_prediction.get("Tahmin_Volatilite", 0.0))
    }
    
    return result