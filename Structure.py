import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
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
            entities_df = entities_df.dropna(subset=['Symbol', 'Security Name'])
            entities_df = entities_df[entities_df['Symbol'].str.isalpha() & (entities_df['Symbol'] != '')]
            entities_df = entities_df[entities_df['Security Name'].str.strip() != '']
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
st.markdown("Select a ticker by searching its symbol or company name.")

# Sidebar for Stock Selection
st.sidebar.header("Stock Selection")

# Load entities from NASDAQ
all_available_entities = load_nasdaq_entities()

# Only Search by Name option
search_query = st.sidebar.text_input("Enter Ticker Symbol or Company Name", "")
ticker_symbol = None

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

            # Price Chart with Selection
            st.subheader(f"{ticker_symbol} Closing Price and Return Analysis")
            close_prices = data[('Close', ticker_symbol)]
            fig_price = px.line(data, x=data.index, y=close_prices, title=f"{ticker_symbol} Closing Price Over Time")
            # Enable selection
            fig_price.update_layout(dragmode='select', selectdirection='h')
            chart = st.plotly_chart(fig_price, use_container_width=True, key="price_chart")

            selected_points = st.session_state.get("price_chart_selection")

            if selected_points and len(selected_points['range']['x']) == 2:
                start_date_selected = datetime.strptime(selected_points['range']['x'][0].split(' ')[0], '%Y-%m-%d').date()
                end_date_selected = datetime.strptime(selected_points['range']['x'][1].split(' ')[0], '%Y-%m-%d').date()

                selected_data = data[(data.index.date >= start_date_selected) & (data.index.date <= end_date_selected)]

                if not selected_data.empty and len(selected_data) > 1:
                    start_price_selected = selected_data[('Close', ticker_symbol)].iloc[0]
                    end_price_selected = selected_data[('Close', ticker_symbol)].iloc[-1]
                    price_change_selected = end_price_selected - start_price_selected
                    percent_change_selected = (price_change_selected / start_price_selected) * 100

                    st.subheader("Return Analysis (Selected Period)")
                    st.metric("Start Price", f"{start_price_selected:.2f}", delta=None)
                    st.metric("End Price", f"{end_price_selected:.2f}", delta=f"{price_change_selected:.2f}")
                    st.metric("Percentage Return", f"{percent_change_selected:.2f}%", delta=None)
                else:
                    st.info("Select a valid range on the chart to analyze the return.")
            else:
                st.info("Drag to select a range on the closing price chart to see return analysis for that period.")


            # Volume Chart (Optional)
            show_volume = st.checkbox("Show Volume Chart")
            if show_volume:
                st.subheader(f"{ticker_symbol} Trading Volume")
                volume_data = data[('Volume', ticker_symbol)]
                fig_volume = px.bar(data, x=data.index, y=volume_data, title=f"{ticker_symbol} Trading Volume Over Time")
                st.plotly_chart(fig_volume, use_container_width=True)

            # Calculate and Display Overall Performance Metrics
            st.subheader("Overall Performance Metrics")
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
                st.info("Not enough data points to calculate overall performance metrics for the selected period.")

        elif period or start_date:
            st.info(f"No data available for {ticker_symbol} for the selected time period.")
    else:
        st.info("Try typing a ticker symbol or company name to search NASDAQ listings.")

st.markdown("---")
st.markdown("Data source: [NASDAQ Trader](ftp://ftp.nasdaqtrader.com/symboldirectory/) and [Yahoo Finance](https://pypi.org/project/yfinance/)")
st.markdown("---")
st.markdown("Data source: [NASDAQ Trader](ftp://ftp.nasdaqtrader.com/symboldirectory/) and [Yahoo Finance](https://pypi.org/project/yfinance/)")
