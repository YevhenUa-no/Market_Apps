import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.title("Stock Performance Dashboard")
st.markdown("Enter a ticker symbol and select a time period to view its performance.")

# Sidebar for Ticker and Time Period Selection
st.sidebar.header("Stock and Time Period")
ticker_symbol = st.sidebar.text_input("Enter Ticker Symbol (e.g., AAPL, MSFT, GOOG)", "AAPL").upper()

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
selected_time = st.sidebar.selectbox("Select Time Period", list(time_options.keys()), index=6)  # Default to 2 Years

start_date = None
end_date = datetime.now().date()
period = None

if selected_time == "Custom":
    start_date = st.sidebar.date_input("Start Date", datetime.now().date() - timedelta(days=365))
    end_date = st.sidebar.date_input("End Date", datetime.now().date())
    if start_date > end_date:
        st.sidebar.error("Error: Start date cannot be after end date.")
        st.stop()
else:
    period = time_options[selected_time]

# Fetch Data
data = None
error_message = None

st.subheader(f"Performance of {ticker_symbol}")

if ticker_symbol:
    if period or start_date:
        with st.spinner(f"Fetching data for {ticker_symbol}..."):
            try:
                if selected_time == "Custom":
                    data = yf.download(ticker_symbol, start=start_date, end=end_date)
                else:
                    data = yf.download(ticker_symbol, period=period)
            except Exception as e:
                error_message = f"An error occurred while fetching data for {ticker_symbol}: {e}"

        if error_message:
            st.error(error_message)
        elif data is not None and not data.empty:
            st.dataframe(data)

            # Price Chart
            st.subheader(f"{ticker_symbol} Closing Price")
            fig_price = px.line(data, x=data.index, y=('Close', ticker_symbol), title=f"{ticker_symbol} Closing Price Over Time")
            st.plotly_chart(fig_price, use_container_width=True)

            # Volume Chart (Optional)
            show_volume = st.checkbox("Show Volume Chart")
            if show_volume:
                st.subheader(f"{ticker_symbol} Trading Volume")
                fig_volume = px.bar(data, x=data.index, y=('Volume', ticker_symbol), title=f"{ticker_symbol} Trading Volume Over Time")
                st.plotly_chart(fig_volume, use_container_width=True)

            # Calculate and Display Performance Metrics
            st.subheader("Performance Metrics")
            if len(data) > 1:
                start_price = data[('Close', ticker_symbol)].iloc[0]
                end_price = data[('Close', ticker_symbol)].iloc[-1]
                price_change = end_price - start_price
                percent_change = (price_change / start_price) * 100

                st.metric("Start Price", f"{start_price:.2f}")
                st.metric("End Price", f"{end_price:.2f}")
                st.metric("Price Change", f"{price_change:.2f}")
                st.metric("Percentage Change", f"{percent_change:.2f}%")
            else:
                st.info("Not enough data points to calculate performance metrics for the selected period.")

        elif period or start_date:
            st.info(f"No data available for {ticker_symbol} for the selected time period.")
    else:
        st.info("Please select a time period in the sidebar.")
else:
    st.info("Please enter a ticker symbol in the sidebar.")

st.markdown("---")
st.markdown("Data provided by Yahoo Finance using the `yfinance` library.")
