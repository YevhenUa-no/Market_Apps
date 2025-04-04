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
            # Corrected line to access the 'Close' column
            fig_price = px.line(data, x=data.index, y=('Close', '^GSPC'), title="S&P 500 Closing Price")
            st.plotly_chart(fig_price, use_container_width=True)
        except ValueError as ve:
            st.error(f"Error creating price chart: {ve}")
        except Exception as e:
            st.error(f"An unexpected error occurred during chart creation: {e}")

        # Volume Chart
        show_volume = st.checkbox("Show Volume Chart")
        if show_volume:
            st.subheader("S&P 500 Trading Volume")
            fig_volume = px.bar(data, x=data.index, y=('Volume', '^GSPC'), title="S&P 500 Trading Volume")
            st.plotly_chart(fig_volume, use_container_width=True)

        # Moving Average
        st.sidebar.header("Technical Indicators")
        show_ma = st.sidebar.checkbox("Show Moving Average")
        if show_ma:
            ma_window = st.sidebar.slider("Moving Average Window (days)", min_value=5, max_value=200, value=20)
            data['MA'] = data[('Close', '^GSPC')].rolling(window=ma_window).mean()
            fig_ma = px.line(data, x=data.index, y=[('Close', '^GSPC'), 'MA'],
                             title=f"S&P 500 Closing Price with {ma_window}-day Moving Average")
            st.plotly_chart(fig_ma, use_container_width=True)

        # Date Range Filter (adjust y-axis access here as well if needed)
        st.sidebar.header("Date Range Filter")
        if len(data.index) > 1:
            min_date = data.index.min().to_pydatetime().date()
            max_date = data.index.max().to_pydatetime().date()
            date_range = st.sidebar.slider("Select Date Range", min_value=min_date, max_value=max_date,
                                           value=(min_date, max_date))

            filtered_data = data[(data.index.date >= date_range[0]) & (data.index.date <= date_range[1])]
            st.subheader("S&P 500 Performance (Filtered)")
            if not filtered_data.empty:
                fig_filtered = px.line(filtered_data, x=filtered_data.index, y=('Close', '^GSPC'),
                                       title="S&P 500 Closing Price (Filtered)")
                st.plotly_chart(fig_filtered, use_container_width=True)
            else:
                st.info("No data available for the selected date range.")
        else:
            st.sidebar.info("Not enough data points for date range filtering.")

    elif period or start_date:
        st.info("No data available for the selected time period.")
else:
    st.info("Select a time period in the sidebar to view the S&P 500 performance.")
