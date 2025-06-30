import streamlit as st

st.title("🎯 Test Ultra Minimal")
st.write("Si vous voyez ce message, Streamlit fonctionne !")

# Test très basique des imports
try:
    import pandas as pd
    st.success("✅ pandas OK")
except Exception as e:
    st.error(f"❌ pandas: {e}")

try:
    import plotly
    st.success("✅ plotly OK") 
except Exception as e:
    st.error(f"❌ plotly: {e}")

st.write("�� Test terminé !") 