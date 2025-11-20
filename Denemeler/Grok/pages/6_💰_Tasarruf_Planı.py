import streamlit as st
hedef = st.number_input("Hedef Tutar (₺)", 1000000)
ay = st.slider("Kaç ayda?", 12, 120, 48)
aylik = hedef / ay * (1 + 0.15)**(ay/12) / ay
st.success(f"Aylık birikim: ₺{aylik:,.0f} → {ay}. ayda {hedef:,.0f} ₺!")