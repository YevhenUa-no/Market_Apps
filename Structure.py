import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- Function to load tickers from NASDAQ and return only Symbol ---
@st.cache_data
def load_nasdaq_symbols():
    url = "ftp://ftp.nasdaqtrader.com/SymbolDirectory/nasdaqlisted.txt"
    try:
        response = pd.read_csv(url, sep="|")  # Let pandas infer the header
        print("Columns in the loaded DataFrame:", response.columns) # Debugging line
        if 'Symbol' in response.columns:
            symbols_df = response[['Symbol']].copy()
            symbols_df = symbols_df[symbols_df['Symbol'].str.isalpha()]
            return sorted(symbols_df['Symbol'].tolist())
        else:
            st.error("Error: 'Symbol' column not found in NASDAQ data.")
            return []
    except Exception as e:
        st.error(f"Failed to load symbols from NASDAQ Trader: {e}")
        return []

# --- Function to search tickers (now searches a list of symbols) ---
@st.cache_data
def search_tickers(query, all_symbols):
    if not query:
        return all_symbols[:5]
    results = [symbol for symbol in all_symbols if query.upper() in symbol]
    return sorted(results)

st.title("Stock Performance Dashboard")
st.markdown("Select a ticker or search by symbol.")

# Sidebar for Ticker Selection
st.sidebar.header("Stock Selection")

# Load tickers from NASDAQ
all_available_symbols = load_nasdaq_symbols()

# Option to select from a dropdown or search
select_option = st.sidebar.radio("Select Ticker By:", ["Dropdown", "Search by Name"])

ticker_symbol = None

if select_option == "Dropdown":
    if all_available_symbols:
        ticker_symbol = st.sidebar.selectbox("Select Ticker", all_available_symbols)
    else:
        st.sidebar.warning("Could not load tickers for the dropdown.")
elif select_option == "Search by Name":
    search_query = st.sidebar.text_input("Enter Ticker Symbol", "")
    if search_query:
        search_results = search_tickers(search_query, all_available_symbols)
        if search_results:
            ticker_symbol = st.sidebar.selectbox("Search Results", search_results)
        else:
            st.sidebar.info("No tickers found matching your search on NASDAQ.")
    else:
        st.sidebar.info("Try typing a ticker symbol to search NASDAQ listings.")

# Sidebar for Time Period Selection (Only show if a ticker is selected)
if ticker_symbol:
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
    selected_time = st.sidebar.selectbox("Select Time Period", list(time_options.keys()), index=6)

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

    if period or start_date:
        with st.spinner(f"Fetching data for {ticker_symbol}..."):
            try:
                data = yf.download(ticker_symbol, start=start_date, end=end_date) if selected_time == "Custom" else yf.download(ticker_symbol, period=period)
            except Exception as e:
                error_message = f"An error occurred while fetching data for {ticker_symbol}: {e}"

        if error_message:
            st.error(error_message)
        elif data is not None and not data.empty:
            st.dataframe(data)

            # Price Chart
            st.subheader(f"{ticker_symbol} Closing Price")
            close_prices = data[('Close', ticker_symbol)]
            fig_price = px.line(data, x=data.index, y=close_prices, title=f"{ticker_symbol} Closing Price Over Time")
            st.plotly_chart(fig_price, use_container_width=True)

            # Volume Chart (Optional)
            show_volume = st.checkbox("Show Volume Chart")
            if show_volume:
                st.subheader(f"{ticker_symbol} Trading Volume")
                volume_data = data[('Volume', ticker_symbol)]
                fig_volume = px.bar(data, x=data.index, y=volume_data, title=f"{ticker_symbol} Trading Volume Over Time")
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
        st.info("Please select a ticker symbol in the sidebar.")

st.markdown("---")
st.markdown("Data provided by Yahoo Finance and NASDAQ Trader.")
