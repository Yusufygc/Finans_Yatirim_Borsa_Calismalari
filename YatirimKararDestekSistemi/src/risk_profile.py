import pandas as pd
import numpy as np

class RiskManager:
    """
    Profesyonel Sinyal Motoru (v2.0)
    Çok Faktörlü Puanlama Sistemi kullanır:
    1. Ensemble Tahmin Trendi (Ağırlık: %50)
    2. Volatilite Riski (Ağırlık: %20)
    3. Teknik Bağlam (RSI ve SMA) (Ağırlık: %30)
    """
    def __init__(self, risk_profile="orta"):
        self.risk_profile = risk_profile
        # Profil bazlı risk toleransı (Puan eşikleri)
        # Agresif yatırımcı SAT için daha çok negatif puana ihtiyaç duyar
        if risk_profile == "agresif":
            self.buy_threshold = 2
            self.sell_threshold = -3
        elif risk_profile == "temkinli":
            self.buy_threshold = 4
            self.sell_threshold = -1
        else: # orta
            self.buy_threshold = 3
            self.sell_threshold = -2

    def generate_signals(self, forecast_df, current_price, current_rsi=None, current_sma=None):
        """
        Tahmin tablosuna 'Sinyal' ve 'Gerekçe' sütunlarını ekler.
        """
        print(f"[INFO] Risk Yönetimi: Puanlama Sistemi Devrede (Profil: {self.risk_profile.upper()})")
        
        signals = []
        reasons = [] # Kararın nedenini açıklayan metin
        
        # Referans fiyatı döngü içinde güncelleyeceğiz
        ref_price = current_price
        
        for index, row in forecast_df.iterrows():
            score = 0
            reason_list = []
            
            # --- FAKTÖR 1: TAHMİN EDİLEN GETİRİ (ENSEMBLE) ---
            predicted_price = row["Final_Ensemble"]
            predicted_return_pct = ((predicted_price - ref_price) / ref_price) * 100
            
            if predicted_return_pct > 2.0:
                score += 3
                reason_list.append("Güçlü Yükseliş Beklentisi")
            elif predicted_return_pct > 0.5:
                score += 1
                reason_list.append("Ilımlı Yükseliş")
            elif predicted_return_pct < -2.0:
                score -= 3
                reason_list.append("Sert Düşüş Beklentisi")
            elif predicted_return_pct < -0.5:
                score -= 1
                reason_list.append("Zayıf Görünüm")
            else:
                reason_list.append("Yatay Seyir")

            # --- FAKTÖR 2: VOLATİLİTE (RİSK) ---
            volatility = row["Tahmin_Volatilite"]
            # Volatilite çok yüksekse (örn > 3.5), alım iştahını düşür, satışı tetikle
            if volatility > 3.5:
                score -= 2
                reason_list.append("Yüksek Risk/Volatilite")
            elif volatility < 1.5:
                score += 1
                reason_list.append("Düşük Risk")

            # --- FAKTÖR 3: TEKNİK BAĞLAM (MEVCUT DURUM) ---
            # Not: Gelecek günlerde RSI tahmini yapmıyoruz, şimdiki RSI durumunu genel bir 'Bias' (Eğilim) olarak ekliyoruz
            if current_rsi is not None:
                if current_rsi < 30: 
                    score += 2 # Aşırı satım bölgesinde, tepki alımı gelebilir
                    reason_list.append("RSI Aşırı Satım")
                elif current_rsi > 70:
                    score -= 2 # Aşırı alım bölgesinde, düzeltme riski
                    reason_list.append("RSI Aşırı Alım")
            
            if current_sma is not None:
                if ref_price > current_sma:
                    score += 1 # Ana trend (SMA50) üzerinde
                else:
                    score -= 1 # Ana trendin altında

            # --- KARAR MEKANİZMASI ---
            if score >= self.buy_threshold:
                final_signal = "AL"
            elif score <= self.sell_threshold:
                final_signal = "SAT"
            else:
                # Arada kalan durumlar: Eğer düşüş bekliyoruz ama SAT eşiğini geçemediysek
                # ve elimizde mal varsa (bunu bilemiyoruz ama varsayalım), panik yapma TUT.
                final_signal = "TUT"
            
            signals.append(final_signal)
            reasons.append(", ".join(reason_list))
            
            # Referans fiyatı bir sonraki gün için güncelle (zincirleme etki)
            ref_price = predicted_price

        forecast_df["Sinyal"] = signals
        forecast_df["Sinyal_Gerekcesi"] = reasons
        return forecast_df