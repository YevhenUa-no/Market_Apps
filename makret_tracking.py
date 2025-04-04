import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

ticker = "^GSPC"  # S&P 500 ticker symbol
data = None
error_message = None

st.subheader("S&P 500 Data")

period = st.session_state.get("period")
start_date = st.session_state.get("start_date")
end_date = st.session_state.get("end_date")
selected_time = st.session_state.get("selected_time")

if period or start_date:
    with st.spinner(f"Fetching S&P 500 data for {selected_time.lower()}..."):
        try:
            if selected_time == "Custom":
                data = yf.download(ticker, start=start_date, end=end_date)
            else:
                data = yf.download(ticker, period=period)
        except Exception as e:
            st.error(f"An error occurred while fetching data: {e}")
            data = pd.DataFrame()

    if data is not None and not data.empty:
        st.dataframe(data)

        st.subheader("S&P 500 Price Performance")
        try:
            fig_price = px.line(data, x=data.index, y="Close", title="S&P 500 Closing Price")
            st.plotly_chart(fig_price, use_container_width=True)
        except ValueError as ve:
            st.error(f"Error creating price chart: {ve}")
        except Exception as e:
            st.error(f"An unexpected error occurred during chart creation: {e}")

        # ... rest of your makret_tracking.py code ...
    elif period or start_date:
        st.info("No data available for the selected time period.")
else:
    st.info("Select a time period in the sidebar to view the S&P 500 performance.")
