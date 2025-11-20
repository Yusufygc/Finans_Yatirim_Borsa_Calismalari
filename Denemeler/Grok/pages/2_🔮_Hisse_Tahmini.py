import streamlit as st
from utils.stock_prediction import predict_price, create_candlestick_with_prediction
st.header("🔎 Hisse Fiyat Tahmini")
ticker = st.selectbox("Hisse Seç", ["SISE.IS", "ASELS.IS", "THYAO.IS", "EREGL.IS"])
if st.button("Tahmin Et"):
    pred = predict_price(ticker)
    st.success(f"Yarın kapanış tahmini: {pred['price']:.2f} ₺")
    st.info(f"Öneri: **{pred['decision']}** – Duygu etkisi: {pred['sentiment']:+.1f}%")
    st.plotly_chart(create_candlestick_with_prediction(ticker), use_container_width=True)