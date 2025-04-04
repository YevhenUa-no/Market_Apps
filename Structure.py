import streamlit as st
print(f"Streamlit version: {st.__version__}")

pg = st.navigation([
    st.Page("makret_tracking.py", name="Market Tracking"),
])
