import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# --- Page config ---
st.set_page_config(page_title="Market Tracker", page_icon=":chart_with_upwards_trend:")

# --- App Content ---
st.title("📈 S&P 500 Market Tracking")

ticker = "^GSPC"
data = None

# Sidebar Inputs (for standalone use)
st.sidebar.header("Time Period Settings")
selected_time = st.sidebar.selectbox("Time Frame", ["1mo", "3mo", "6mo", "YTD", "1y", "5y", "Max", "Custom"])
period = None
start_date = None
end_date = None

if selected_time == "Custom":
    start_date = st.sidebar.date_input("Start Date")
    end_date = st.sidebar.date_input("End Date")
else:
    period = selected_time

# Download and display data
if period or (start_date and end_date):
    with st.spinner("Fetching S&P 500 data..."):
        try:
            if selected_time == "Custom":
                data = yf.download(ticker, start=start_date, end=end_date)
            else:
                data = yf.download(ticker, period=period)
        except Exception as e:
            st.error(f"An error occurred while fetching data: {e}")
            data = pd.DataFrame()

    if data is not None and not data.empty:
        st.subheader("Raw Data")
        st.dataframe(data)

        # Price chart
        st.subheader("Price Chart")
        try:
            fig_price = px.line(data, x=data.index, y="Close", title="S&P 500 Closing Price")
            st.plotly_chart(fig_price, use_container_width=True)
        except Exception as e:
            st.error(f"Chart creation error: {e}")

        # Volume chart
        if st.checkbox("Show Volume Chart"):
            st.subheader("Trading Volume")
            fig_volume = px.bar(data, x=data.index, y="Volume", title="S&P 500 Trading Volume")
            st.plotly_chart(fig_volume, use_container_width=True)

        # Moving average
        st.sidebar.header("Technical Indicators")
        if st.sidebar.checkbox("Show Moving Average"):
            ma_window = st.sidebar.slider("MA Window (days)", 5, 200, 20)
            data["MA"] = data["Close"].rolling(window=ma_window).mean()
            fig_ma = px.line(data, x=data.index, y=["Close", "MA"],
                             title=f"S&P 500 with {ma_window}-Day Moving Average")
            st.plotly_chart(fig_ma, use_container_width=True)

        # Date range filter
        st.sidebar.header("Filter by Date")
        if len(data.index) > 1:
            min_date = data.index.min().date()
            max_date = data.index.max().date()
            date_range = st.sidebar.slider("Select Range", min_value=min_date, max_value=max_date,
                                           value=(min_date, max_date))
            filtered = data[(data.index.date >= date_range[0]) & (data.index.date <= date_range[1])]

            st.subheader("Filtered Performance")
            if not filtered.empty:
                fig_filtered = px.line(filtered, x=filtered.index, y="Close", title="Filtered Closing Price")
                st.plotly_chart(fig_filtered, use_container_width=True)
            else:
                st.info("No data available for the selected date range.")
    else:
        st.info("No data returned for selected time frame.")
else:
    st.info("Please select a time period to load data.")
