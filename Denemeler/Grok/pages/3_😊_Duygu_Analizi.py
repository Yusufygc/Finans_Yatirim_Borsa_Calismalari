import streamlit as st
st.header("😊 Gerçek Zamanlı Piyasa Duygusu")
col1, col2 = st.columns(2)
with col1:
    st.metric("Son 24 saatte analiz", "42.891 tweet")
with col2:
    st.metric("Genel Duygu", "%68 Pozitif")

sentiment_df = get_live_sentiment()
st.bar_chart(sentiment_df.set_index('saat')['duygu_skoru'])
st.dataframe(top_negative_tweets, height=300)