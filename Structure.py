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

        initial_investment_amount = st.sidebar.number_input("Initial Investment Amount ($)", min_value=100, step=100, value=1000)
        monthly_investment_amount = st.sidebar.number_input("Monthly Investment Amount ($)", min_value=10, step=10, value=200)

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
            investment_dates_monthly = pd.to_datetime(investment_data.resample("MS").first().index)
            investment_schedule = {date.strftime("%Y-%m-%d"): monthly_investment_amount for date in investment_dates_monthly if date >= pd.to_datetime(investment_date)}
            investment_schedule[investment_date.strftime("%Y-%m-%d")] = investment_schedule.get(investment_date.strftime("%Y-%m-%d"), 0) + initial_investment_amount

            portfolio_value_monthly = pd.Series(index=investment_data.index, dtype=float)
            total_shares_monthly = 0
            total_invested_monthly = 0

            for date, price in investment_data[close_col].items():
                investment_on_date = investment_schedule.get(date.strftime("%Y-%m-%d"), 0)
                if investment_on_date > 0:
                    shares_bought = investment_on_date / price
                    total_shares_monthly += shares_bought
                    total_invested_monthly += investment_on_date
                portfolio_value_monthly[date] = total_shares_monthly * price

            portfolio_df_monthly = pd.DataFrame({'Value': portfolio_value_monthly})
            portfolio_df_monthly = portfolio_df_monthly.dropna()
            final_value_monthly = portfolio_df_monthly['Value'].iloc[-1] if not portfolio_df_monthly.empty else 0

            # --- Comparison Chart Starting from Investment Date ---
            comparison_df_invested = pd.DataFrame({
                'Date': investment_data.index,
                'Invest Full Sum Initially': investment_data['FullSumValue'],
                'Invest Part Monthly': portfolio_df_monthly['Value'].reindex(investment_data.index, method='pad')
            })

            fig_comparison_invested = px.line(comparison_df_invested, x='Date', y=['Invest Full Sum Initially', 'Invest Part Monthly'],
                                             title=f"Comparison Since Investment Date: {investment_date.date()}")
            fig_comparison_invested.update_yaxes(title_text="Portfolio Value ($)")
            st.plotly_chart(fig_comparison_invested, use_container_width=True)

            # --- Comparison Summary ---
            st.subheader("💰 Comparison Summary")
            col1, col2 = st.columns(2)
            col1.metric("Final Value (Full Sum)", f"${final_value_full:,.2f}")
            col2.metric("Final Value (Part Monthly)", f"${final_value_monthly:,.2f}")

            initial_total_investment = initial_investment_amount
            total_monthly_contributions = monthly_investment_amount * (len(investment_schedule) - 1) if len(investment_schedule) > 1 else 0
            total_invested_monthly_calc = initial_total_investment + total_monthly_contributions

            col3, col4 = st.columns(2)
            col3.metric("Total Invested (Full Sum)", f"${total_investment_full:,.2f}")
            col4.metric("Total Invested (Part Monthly)", f"${total_invested_monthly_calc:,.2f}")

        else:
            st.warning(f"No data available on or after the selected investment date: {investment_date}")

else:
    st.info("Please select a stock to begin.")
