import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- Function to fetch available tickers from yfinance info ---
@st.cache_data
def get_yahoo_tickers_from_info():
    try:
        # Get information for a known popular ticker to access the 'info' dictionary
        aapl_info = yf.Ticker("AAPL").info
        if 'symbol' in aapl_info and 'exchange' in aapl_info:
            exchange = aapl_info['exchange']
            # This is a very basic and potentially incomplete way.
            # There isn't a direct API call to get *all* symbols.
            # This attempts to get symbols associated with a major exchange.
            # The 'exchange' key might not always provide a direct way to list symbols.
            # This approach is limited and might not be reliable.
            if exchange in ["NMS", "NYQ", "AMEX"]:  # Common US exchanges
                # This is still a simplification. A true list requires a dedicated API.
                # We'll return a placeholder message as direct API access is limited.
                return ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "JPM", "V", "JNJ", "META"]
            else:
                return ["AAPL", "MSFT", "GOOGL"] # Default if exchange is not recognized
        else:
            return ["AAPL", "MSFT", "GOOGL"] # Default if basic info is missing
    except Exception as e:
        st.error(f"Error fetching ticker information: {e}")
        return ["AAPL", "MSFT", "GOOGL"] # Default on error

# --- Function to search tickers by name (Simplified - now used for suggestions) ---
@st.cache_data
def search_tickers(query, all_tickers):
    if not query:
        return all_tickers[:5]  # Show a few suggestions initially
    results = [ticker for ticker in all_tickers if query.upper() in ticker]
    return sorted(results)

st.title("Stock Performance Dashboard")
st.markdown("Select a ticker or search by name to view its performance.")

# Sidebar for Ticker Selection
st.sidebar.header("Stock Selection")

# Option to select from a dropdown or search
select_option = st.sidebar.radio("Select Ticker By:", ["Dropdown", "Search by Name"])

all_available_tickers = get_yahoo_tickers_from_info()
ticker_symbol = None

if select_option == "Dropdown":
    ticker_symbol = st.sidebar.selectbox("Select Ticker", all_available_tickers)
elif select_option == "Search by Name":
    search_query = st.sidebar.text_input("Enter Company Name or Ticker Fragment", "")
    if search_query:
        search_results = search_tickers(search_query, all_available_tickers)
        if search_results:
            ticker_symbol = st.sidebar.selectbox("Search Results", search_results)
        elif search_query:  # Only show "No tickers found" if there was a query
            st.sidebar.info("No tickers found matching your search.")
    else:
        st.sidebar.info(f"Try typing a company name or ticker. Here are a few suggestions: {', '.join(all_available_tickers[:5])}")

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
        st.info("Please select a time period in the sidebar.")

else:
    st.info("Please select a ticker symbol in the sidebar.")

st.markdown("---")
st.markdown("Data provided by Yahoo Finance using the `yfinance` library.")
