import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.title("S&P 500 Performance Dashboard")
st.markdown("Get historical S&P 500 data and visualize its performance.")

# Interactive features

# Time period selection
st.sidebar.header("Time Period")
time_options = {
    "1 Day": "1d",
    "5 Days": "5d",
    "1 Month": "1mo",
    "3 Months": "3mo",
    "6 Months": "6mo",
    "1 Year": "1y",
    "2 Years": "2y",
    "5 Years": "5y",
    "10 Years": "10y",
    "Year-to-Date": "ytd",
    "Max": "max",
    "Custom": "custom",
}
selected_time = st.sidebar.selectbox("Select Time Period", list(time_options.keys()))

start_date = None
end_date = datetime.now().date()

if selected_time == "Custom":
    start_date = st.sidebar.date_input("Start Date", datetime.now().date() - timedelta(days=365))
    end_date = st.sidebar.date_input("End Date", datetime.now().date())
    if start_date > end_date:
        st.sidebar.error("Error: Start date cannot be after end date.")
        st.stop()
    period = None
else:
    period = time_options[selected_time]

# Data fetching
ticker = "^GSPC"  # S&P 500 ticker symbol
data = None
error_message = None

st.subheader("S&P 500 Data")

if period or start_date:
    with st.spinner(f"Fetching S&P 500 data for {selected_time.lower()}..."):
        try:
            if selected_time == "Custom":
                data = yf.download(ticker, start=start_date, end=end_date)
            else:
                data = yf.download(ticker, period=period)
        except Exception as e:
            error_message = f"An error occurred while fetching data: {e}"

    if error_message:
        st.error(error_message)
    elif data is not None and not data.empty:
        st.dataframe(data)

        # Price Chart
        st.subheader("S&P 500 Price Performance")
        fig_price = px.line(data, x=data.index, y="Close", title="S&P 500 Closing Price")
        st.plotly_chart(fig_price, use_container_width=True)

        # Volume Chart (Interactive Feature)
        show_volume = st.checkbox("Show Volume Chart")
        if show_volume:
            st.subheader("S&P 500 Trading Volume")
            fig_volume = px.bar(data, x=data.index, y="Volume", title="S&P 500 Trading Volume")
            st.plotly_chart(fig_volume, use_container_width=True)

        # Moving Average (Interactive Feature)
        st.sidebar.header("Technical Indicators")
        show_ma = st.sidebar.checkbox("Show Moving Average")
        if show_ma:
            ma_window = st.sidebar.slider("Moving Average Window (days)", min_value=5, max_value=200, value=20)
            data['MA'] = data['Close'].rolling(window=ma_window).mean()
            fig_ma = px.line(data, x=data.index, y=['Close', 'MA'],
                             title=f"S&P 500 Closing Price with {ma_window}-day Moving Average")
            st.plotly_chart(fig_ma, use_container_width=True)

        # Date Range Slider (Interactive Feature)
        st.sidebar.header("Date Range Filter")
        if len(data.index) > 1:
            min_date = data.index.min().to_pydatetime().date()
            max_date = data.index.max().to_pydatetime().date()
            date_range = st.sidebar.slider("Select Date Range", min_value=min_date, max_value=max_date,
                                           value=(min_date, max_date))

            filtered_data = data[(data.index.date >= date_range[0]) & (data.index.date <= date_range[1])]
            st.subheader("S&P 500 Performance (Filtered)")
            if not filtered_data.empty:
                fig_filtered = px.line(filtered_data, x=filtered_data.index, y="Close",
                                       title="S&P 500 Closing Price (Filtered)")
                st.plotly_chart(fig_filtered, use_container_width=True)
            else:
                st.info("No data available for the selected date range.")
        else:
            st.sidebar.info("Not enough data points for date range filtering.")

    elif period or start_date:
        st.info("No data available for the selected time period.")
else:
    st.info("Select a time period to view the S&P 500 performance.")

st.markdown("---")
st.markdown("Data source: Yahoo Finance (using the `yfinance` library)")
st.markdown("Interactive features include selecting the time period, showing volume, adding a moving average, and filtering by date range.")
