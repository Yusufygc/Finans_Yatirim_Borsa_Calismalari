# app.py
import streamlit as st
st.set_page_config(page_title="BIST Yatırım Asistanı", layout="wide", page_icon="📈")

st.title("📈 BIST Yatırım Asistanı – AI Destekli Küçük Yatırımcı Koruyucusu")
st.markdown("**Muhammed Yusuf Yağcı** • TÜBİTAK 2209-A • 2025")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Portföy Değeri", "₺248.750", "+₺8.240 (+3.42%)")
with col2:
    st.metric("Risk Profili", "Orta-Agresif", "↑ 1 seviye")
with col3:
    st.metric("Piyasa Duygusu", "%68 Pozitif", "🟢")

st.plotly_chart(fig_bist100_live, use_container_width=True)
st.info("🚀 Bugün en çok konuşulan: #SISE #ASELS #THYAO – Duygu skoru %82'ye ulaştı!")