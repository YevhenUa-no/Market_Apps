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

st.title("Stock Performance Dashboard")
st.markdown("Select a ticker from the dropdown and analyze its performance.")

# Sidebar for Stock Selection
st.sidebar.header("Stock Selection")

# Load entities from NASDAQ
all_available_entities = load_nasdaq_entities()

# Only Dropdown option
if all_available_entities:
    selected_entity = st.sidebar.selectbox("Select Ticker", all_available_entities, format_func=lambda x: f"{x[0]}")
    if selected_entity:
        ticker_symbol = selected_entity[1]
    else:
        st.sidebar.warning("Could not load tickers for the dropdown.")
        ticker_symbol = None
else:
    st.sidebar.warning("Could not load tickers for the dropdown.")
    ticker_symbol = None

# Sidebar for Investment Analysis
st.sidebar.header("Investment Analysis")
investment_date_str = st.sidebar.date_input("Investment Date", datetime(2024, 1, 1).date())
investment_amount = st.sidebar.number_input("Investment Amount", min_value=1.0, value=1000.0, step=100.0)

# Sidebar for Time Period Selection (Only show if a ticker is selected)
if ticker_symbol:
    st.sidebar.header("Time Period")
    today = datetime(2025, 4, 6).date()  # Using today's date as per the context
    time_options = {
        "1 Month": "1mo",
        "3 Months": "3mo",
        "6 Months": "6mo",
        "1 Year": "1y",
        "2 Years": "2y",
        "5 Years": "5y",
        "Max": "max",
        "Custom": "custom",
    }
    default_index = 3  # Default to 1 Year
    selected_time = st.sidebar.selectbox("Select Time Period", list(time_options.keys()), index=default_index)

    start_date = None
    end_date = today
    period = None

    # Adjust start date if investment date is later than selected start
    if isinstance(investment_date_str, datetime):
        investment_date = investment_date_str.date()
    else:
        investment_date = investment_date_str

    if selected_time == "Custom":
        start_date = st.sidebar.date_input("Start Date", today - timedelta(days=365))
        end_date = st.sidebar.date_input("End Date", today)
        if start_date > end_date:
            st.sidebar.error("Error: Start date cannot be after end date.")
            st.stop()
    else:
        if period:
            if period == "1d":
                duration = pd.Timedelta(days=1)
            elif period == "5d":
                duration = pd.Timedelta(days=5)
            elif period == "1mo":
                duration = pd.DateOffset(months=1)
            elif period == "3mo":
                duration = pd.DateOffset(months=3)
            elif period == "6mo":
                duration = pd.DateOffset(months=6)
            elif period == "1y":
                duration = pd.DateOffset(years=1)
            elif period == "2y":
                duration = pd.DateOffset(years=2)
            elif period == "5y":
                duration = pd.DateOffset(years=5)
            elif period == "10y":
                duration = pd.DateOffset(years=10)
            elif period == "ytd":
                start_date = datetime(today.year, 1, 1).date()
            elif period == "max":
                start_date = None # Handled by yfinance
            else:
                duration = pd.Timedelta(days=30) # Default to 30 days if unknown
            if period != "ytd" and period != "max":
                start_date = today - duration
        else:
            start_date = investment_date # Default to investment date if no period selected

    # Adjust start date if investment date is later than selected start
    if start_date and investment_date > start_date:
        start_date = investment_date

    # Fetch Data
    data = None
    error_message = None

    st.subheader(f"Performance of {ticker_symbol}")

    if start_date and end_date:
        with st.spinner(f"Fetching data for {ticker_symbol}..."):
            try:
                data = yf.download(ticker_symbol, start=start_date, end=end_date)
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
                    start_price_selected = selected_data.loc[selected_data.index[0], ('Close', ticker_symbol)]
                    end_price_selected = selected_data.loc[selected_data.index[-1], ('Close', ticker_symbol)]
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

            # Investment Development Analysis
            st.subheader("Investment Development")
            investment_date = pd.to_datetime(investment_date_str)

            if investment_date.date() >= data.index.min().date() and investment_date.date() <= data.index.max().date():
                initial_price = data.loc[investment_date, ('Close', ticker_symbol)]
                investment_timeline = data[data.index >= investment_date].copy()
                investment_timeline['Value'] = (investment_timeline.loc[:, ('Close', ticker_symbol)] / initial_price) * investment_amount

                fig_investment = px.line(investment_timeline, x=investment_timeline.index, y='Value',
                                         title=f"Development of ${investment_amount} Investment in {ticker_symbol}")
                fig_investment.update_yaxes(title_text="Estimated Investment Value ($)")
                st.plotly_chart(fig_investment, use_container_width=True)
            else:
                st.warning(f"Investment date ({investment_date.date()}) is outside the available data range ({data.index.min().date()} to {data.index.max().date()}).")


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
                start_price = data.loc[data.index[0], ('Close', ticker_symbol)]
                end_price = data.loc[data.index[-1], ('Close', ticker_symbol)]
                price_change = end_price - start_price
                percent_change = (price_change / start_price) * 100

                st.metric("Start Price", f"{start_price:.2f}")
                st.metric("End Price", f"{end_price:.2f}")
                st.metric("Price Change", f"{price_change:.2f}")
                st.metric("Percentage Change", f"{percent_change:.2f}%")
            else:
                st.info("Not enough data points to calculate overall performance metrics for the selected period.")

        elif start_date and end_date:
            st.info(f"No data available for {ticker_symbol} for the selected time period.")
    else:
        st.info("Please select a ticker symbol in the sidebar.")

st.markdown("---")
st.markdown(f"Data as of: {datetime(2025, 4, 6).strftime('%Y-%m-%d')} (Contextual)")
st.markdown("Data source: [NASDAQ Trader](ftp://ftp.nasdaqtrader.com/symboldirectory/) and [Yahoo Finance](https://pypi.org/project/yfinance/)")
