import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- Function to load tickers from NASDAQ ---
@st.cache_data
def load_tickers_from_nasdaq():
    url = "ftp://ftp.nasdaqtrader.com/SymbolDirectory/nasdaqlisted.txt"
    try:
        df = pd.read_csv(url, sep="|")
        df = df[["Symbol", "Security Name"]].rename(columns={"Security Name": "Name"})
        df = df[df["Symbol"].str.isalpha()]  # Filter out test/listed-only symbols
        return df
    except Exception as e:
        st.error(f"Failed to load tickers from NASDAQ Trader: {e}")
        return pd.DataFrame(columns=["Symbol", "Name"])

# --- Function to search tickers ---
@st.cache_data
def search_tickers(query, all_tickers_df):
    if not query:
        return all_tickers_df.head(5)
    results = all_tickers_df[all_tickers_df['Symbol'].str.contains(query.upper(), na=False) |
                              all_tickers_df['Name'].str.contains(query, case=False, na=False)]
    return results

st.title("Stock Performance Dashboard")
st.markdown("Select a ticker or search by name to view its performance.")

# Load tickers from NASDAQ
nasdaq_tickers_df = load_tickers_from_nasdaq()
all_available_tickers = nasdaq_tickers_df['Symbol'].tolist()

# Sidebar for Ticker Selection
st.sidebar.header("Stock Selection")

# Option to select from a dropdown or search
select_option = st.sidebar.radio("Select Ticker By:", ["Dropdown", "Search by Name"])

ticker_symbol = None

if select_option == "Dropdown":
    if all_available_tickers:
        ticker_symbol = st.sidebar.selectbox("Select Ticker", sorted(all_available_tickers))
    else:
        st.sidebar.warning("Could not load tickers for the dropdown.")
elif select_option == "Search by Name":
    search_query = st.sidebar.text_input("Enter Company Name or Ticker Fragment", "")
    if search_query:
        search_results_df = search_tickers(search_query, nasdaq_tickers_df)
        if not search_results_df.empty:
            selected_ticker_info = st.sidebar.selectbox(
                "Search Results",
                search_results_df['Symbol'].tolist(),
                format_func=lambda symbol: f"{symbol} ({nasdaq_tickers_df.loc[nasdaq_tickers_df['Symbol'] == symbol, 'Name'].iloc[0]})"
            )
            ticker_symbol = selected_ticker_info
        else:
            st.sidebar.info("No tickers found matching your search on NASDAQ.")
    else:
        st.sidebar.info("Try typing a company name or ticker to search NASDAQ listings.")

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
