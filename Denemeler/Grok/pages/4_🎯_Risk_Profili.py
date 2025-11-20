import streamlit as st
risk = st.slider("Risk İştahınız", 1, 10, 6)
if st.button("Optimize Et"):
    opt = markowitz_optimize(user_portfolio, risk)
    st.pyplot(plot_efficient_frontier(opt))
    st.success(f"Önerilen Dağılım → Hisse: {opt['hisse']}% | Altın: {opt['altin']}%")