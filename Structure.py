import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta  # Ensure this line is present
import io

# --- Function to load tickers from NASDAQ and return Symbol and Security Name ---
@st.cache_data
def load_nasdaq_entities():
    url = "ftp://ftp.nasdaqtrader.com/SymbolDirectory/nasdaqlisted.txt"
    try:
        response = pd.read_csv(url, sep="|")
        print("Columns in the loaded DataFrame:", response.columns) # Debugging line
        if 'Symbol' in response.columns and 'Security Name' in response.columns:
            entities_df = response[['Symbol', 'Security Name']].copy()
            # Remove rows where 'Symbol' or 'Security Name' is NaN or empty
            entities_df = entities_df.dropna(subset=['Symbol', 'Security Name'])
            entities_df = entities_df[entities_df['Symbol'].str.isalpha() & (entities_df['Symbol'] != '')]
            entities_df = entities_df[entities_df['Security Name'].str.strip() != '']
            # Create a combined identifier for the dropdown
            entities_df['Identifier'] = entities_df['Symbol'] + ' - ' + entities_df['Security Name']
            return sorted(entities_df[['Identifier', 'Symbol']].values.tolist())
        else:
            st.error("Error: 'Symbol' and/or 'Security Name' column not found in NASDAQ data.")
            return []
    except Exception as e:
        st.error(f"Failed to load entities from NASDAQ Trader: {e}")
        return []

# --- Function to search tickers (now searches based on Identifier) ---
@st.cache_data
def search_entities(query, all_entities):
    if not query:
        return all_entities[:5]
    results = [entity for entity in all_entities if query.upper() in entity[0].upper()]
    return sorted(results)

st.title("Stock Performance Dashboard")
st.markdown("Select a ticker or search by symbol or company name.")

# Sidebar for Entity Selection
st.sidebar.header("Stock Selection")

# Load entities from NASDAQ
all_available_entities = load_nasdaq_entities()

# Option to select from a dropdown or search
select_option = st.sidebar.radio("Select Ticker By:", ["Dropdown", "Search by Name"])

ticker_symbol = None

if select_option == "Dropdown":
    if all_available_entities:
        selected_entity = st.sidebar.selectbox("Select Ticker", all_available_entities, format_func=lambda x: f"{x[0]}")
        if selected_entity:
            ticker_symbol = selected_entity[1]
    else:
        st.sidebar.warning("Could not load tickers for the dropdown.")
elif select_option == "Search by Name":
    search_query = st.sidebar.text_input("Enter Ticker Symbol or Company Name", "")
    if search_query:
        search_results = search_entities(search_query, all_available_entities)
        if search_results:
            selected_entity = st.sidebar.selectbox("Search Results", search_results, format_func=lambda x: f"{x[0]}")
            if selected_entity:
                ticker_symbol = selected_entity[1]
        else:
            st.sidebar.info("No tickers found matching your search on NASDAQ.")
    else:
        st.sidebar.info("Try typing a ticker symbol or company name to search NASDAQ listings.")

# --- Rest of your Streamlit app code for time period selection and data display ---
# ... (Keep the rest of your code for time period selection, fetching data with yfinance,
#      plotting, and displaying metrics. The 'ticker_symbol' variable will now hold
#      the selected ticker symbol from the dropdown or search.)
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
st.markdown("Data source: [NASDAQ Trader](ftp://ftp.nasdaqtrader.com/symboldirectory/) and [Yahoo Finance](https://pypi.org/project/yfinance/)")

st.markdown("---")
st.markdown("Data source: [NASDAQ Trader](ftp://ftp.nasdaqtrader.com/symboldirectory/) and [Yahoo Finance](https://pypi.org/project/yfinance/)")
