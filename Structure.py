import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="📈 Stock Investment Tracker", layout="wide")

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

# Title
st.title("📈 Stock Investment Dashboard")

# Sidebar: Stock Selection
st.sidebar.header("Select Stock")
all_available_entities = load_nasdaq_entities()

if all_available_entities:
    selected_entity = st.sidebar.selectbox("Choose a stock", all_available_entities, format_func=lambda x: f"{x[0]}")
    if selected_entity:
        ticker_symbol = selected_entity[1]
    else:
        st.sidebar.warning("Could not load tickers for the dropdown.")
        ticker_symbol = None
else:
    st.sidebar.warning("Could not load tickers for the dropdown.")
    ticker_symbol = None

if ticker_symbol:
    ticker = yf.Ticker(ticker_symbol)
    data = ticker.history(period="2y")

    if data.empty:
        st.warning("No data available for the selected ticker.")
    else:
        data = data.dropna()
        data.index = pd.to_datetime(data.index)

        # Only valid trading dates
        available_dates = data.index.normalize().unique()
        available_dates = available_dates.sort_values(ascending=False)

        # Sidebar: Investment input
        st.sidebar.header("Investment Setup")
        investment_date = st.sidebar.selectbox(
            "Select Initial Investment Date (only trading days):",
            options=available_dates,
            format_func=lambda x: x.strftime("%Y-%m-%d")
        )

        initial_investment_amount = st.sidebar.number_input("Initial Investment Amount (<span class="math-inline">\)", min\_value\=100, step\=100, value\=1000\)
monthly\_investment\_amount \= st\.sidebar\.number\_input\("Monthly Investment Amount \(</span>)", min_value=10, step=10, value=1000) # Changed default to match screenshot

        close_col = "Close"

        # Filter data from the investment date onwards
        investment_data = data[data.index >= pd.to_datetime(investment_date)].copy()

        if not investment_data.empty:
            # --- Scenario 1: Invest Whole Sum Initially ---
            initial_price_full = investment_data.loc[pd.to_datetime(investment_date), close_col]
            num_months = (investment_data.index[-1].year - investment_date.year) * 12 + (investment_data.index[-1].month - investment_date.month)
            total_investment_full = initial_investment_amount + (monthly_investment_amount * num_months)
            investment_data['FullSumValue'] = (investment_data[close_col] / initial_price_full) * total_investment_full
            final_value_full = investment_data['FullSumValue'].iloc[-1]

            # --- Scenario 2: Invest Part Monthly ---
            monthly_investment_dates = pd.date_range(start=investment_date, end=investment_data.index[-1], freq='MS')
            investment_schedule = {date.strftime("%Y-%m-%d"): monthly_investment_amount for date in monthly_investment_dates}
            investment_schedule[investment_date.strftime("%Y-%m-%d")] = investment_schedule.get(investment_date.strftime("%Y-%m-%d"), 0) + initial_investment_amount

            monthly_data = {}
            total_shares_monthly = 0
            total_invested_monthly_calc = 0

            processed_months = set()

            sorted_investment_data = investment_data.sort_index()

            for scheduled_date_str in sorted(investment_schedule.keys()):
                scheduled_date = pd.to_datetime(scheduled_date_str)
                month_year_str = scheduled_date.strftime("%Y-%m")

                if month_year_str not in processed_months:
                    # Find the first available trading day in investment_data for this month
                    first_available_date = None
                    first_available_price = None
                    for date, price in sorted_investment_data[close_col].items():
                        if date.year == scheduled_date.year and date.month == scheduled_date.month:
                            first_available_date = date
                            first_available_price = price
                            break

                    if first_available_date is not None:
                        investment_on_schedule = investment_schedule.get(scheduled_date_str, 0)
                        if investment_on_schedule > 0:
                            shares_bought = investment_on_schedule / first_available_price
                            total_shares_monthly += shares_bought
                            total_invested_monthly_calc += investment_on_schedule
                        monthly_data[month_year_str] = [first_available_date.strftime("%Y-%m-%d"), total_invested_monthly_calc, total_shares_monthly * first_available_price]
                        processed_months.add(month_year_str)

            accumulated_df_monthly = pd.DataFrame(monthly_data.values(), columns=['Date', 'Total Invested', 'Portfolio Value'])
            accumulated_df_monthly = accumulated_df_monthly.sort_values(by='Date').reset_index(drop=True)

            # Calculate final portfolio value for the chart
            portfolio_value_monthly_ts = pd.Series(index=investment_data.index, dtype=float)
            total_shares_chart = 0
            total_invested_chart = 0
            initial_price_chart = investment_data.loc[pd.to_datetime(investment_date), close_col]
            total_invested_chart += initial_investment_amount
            total_shares_chart += initial_investment_amount / initial_price_chart
            portfolio_value_monthly_ts[pd.to_datetime(investment_date)] = total_shares_chart * initial_price_chart

            monthly_investment_dates_chart = pd.date_range(start=investment_date, end=investment_data.index[-1], freq='MS')
            investment_schedule_chart = {date.strftime("%Y-%m-%d"): monthly_investment_amount for date in monthly_investment_dates_chart}
