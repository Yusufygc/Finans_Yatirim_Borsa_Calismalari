import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="BIST Yatırım Asistanı", layout="wide", page_icon="📈")

st.sidebar.title("🧭 Menü")
page = st.sidebar.radio("Sayfa Seçiniz", [
    "Ana Sayfa",
    "🔮 Hisse Fiyat Tahmini",
    "😊 Duygu Analizi",
    "🎯 Risk Profili",
    "💰 Tasarruf Planı"
])

# --- ANA SAYFA ---
if page == "Ana Sayfa":
    st.title("📈 BIST Yatırım Asistanı – AI Destekli Küçük Yatırımcı Koruyucusu")
    st.markdown("**Muhammed Yusuf Yağcı** • TÜBİTAK 2209-A • 2025")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Portföy Değeri", "₺248.750", "+₺8.240 (+3.42%)")
    with col2:
        st.metric("Risk Profili", "Orta-Agresif", "↑ 1 seviye")
    with col3:
        st.metric("Piyasa Duygusu", "%68 Pozitif", "🟢")

    # Sahte BIST100 verisi
    dates = pd.date_range("2024-01-01", periods=30)
    prices = np.cumsum(np.random.randn(30)) + 5000
    fig = go.Figure(go.Scatter(x=dates, y=prices, mode="lines", name="BIST100"))
    fig.update_layout(title="BIST100 Endeksi (Gösterim)", yaxis_title="Değer (₺)")
    st.plotly_chart(fig, use_container_width=True)
    st.info("🚀 Bugün en çok konuşulan: #SISE #ASELS #THYAO – Duygu skoru %82'ye ulaştı!")

# --- HİSSE FİYAT TAHMİNİ ---
elif page == "🔮 Hisse Fiyat Tahmini":
    st.header("🔎 Hisse Fiyat Tahmini")
    ticker = st.selectbox("Hisse Seç", ["SISE.IS", "ASELS.IS", "THYAO.IS", "EREGL.IS"])
    if st.button("Tahmin Et"):
        fake_price = np.random.uniform(50, 250)
        sentiment = np.random.uniform(-5, 10)
        decision = np.random.choice(["AL", "TUT", "SAT"])
        st.success(f"Yarın kapanış tahmini: {fake_price:.2f} ₺")
        st.info(f"Öneri: **{decision}** – Duygu etkisi: {sentiment:+.1f}%")

        # Sahte mum grafiği
        days = pd.date_range("2025-01-01", periods=30)
        close = np.cumsum(np.random.randn(30)) + 100
        fig = go.Figure(data=[go.Candlestick(
            x=days,
            open=close - np.random.uniform(1,3,30),
            high=close + np.random.uniform(1,3,30),
            low=close - np.random.uniform(1,3,30),
            close=close
        )])
        fig.update_layout(title=f"{ticker} Hisse Grafiği (Simülasyon)")
        st.plotly_chart(fig, use_container_width=True)

# --- DUYGU ANALİZİ ---
elif page == "😊 Duygu Analizi":
    st.header("😊 Gerçek Zamanlı Piyasa Duygusu (Örnek)")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Analiz Edilen Tweet Sayısı", "42.891")
    with col2:
        st.metric("Genel Duygu", "%68 Pozitif")

    # Sahte veri
    hours = [f"{h}:00" for h in range(0, 24)]
    scores = np.random.uniform(-10, 10, 24)
    sentiment_df = pd.DataFrame({"saat": hours, "duygu_skoru": scores})
    st.bar_chart(sentiment_df.set_index("saat")["duygu_skoru"])
    st.dataframe(pd.DataFrame({
        "Tweet": ["Borsa bugün çok hareketli!", "Hisseler dibe vurdu, panik var.", "Uzun vadede umutluyum!"],
        "Duygu": ["Pozitif", "Negatif", "Pozitif"]
    }), height=200)

# --- RİSK PROFİLİ ---
elif page == "🎯 Risk Profili":
    st.header("🎯 Yatırımcı Risk Profili (Gösterim)")
    risk = st.slider("Risk İştahınız", 1, 10, 6)
    if st.button("Optimize Et"):
        hisse = 60 + (risk - 5) * 2
        altin = 100 - hisse
        st.pyplot()
        st.success(f"Önerilen Dağılım → Hisse: %{hisse:.1f} | Altın: %{altin:.1f}")

        # Sahte Efficient Frontier grafiği
        x = np.linspace(0, 0.3, 50)
        y = 0.05 + 0.4*x - 0.8*x**2
        st.line_chart(pd.DataFrame({"Risk": x, "Getiri": y}))

# --- TASARRUF PLANI ---
elif page == "💰 Tasarruf Planı":
    st.header("💰 Tasarruf Planı Hesaplayıcı")
    hedef = st.number_input("Hedef Tutar (₺)", 100000, 10000000, 1000000, step=50000)
    ay = st.slider("Kaç ayda?", 12, 120, 48)
    aylik = hedef / ay * (1 + 0.15)**(ay/12) / ay
    st.success(f"Aylık birikim: ₺{aylik:,.0f} → {ay}. ayda {hedef:,.0f} ₺ birikir.")
