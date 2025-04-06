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

        # --- Scenario 1: Invest Whole Sum Initially ---
        initial_price_full = data.loc[investment_date, close_col]
        num_months = (data.index[-1].year - investment_date.year) * 12 + (data.index[-1].month - investment_date.month)
        total_investment_full = initial_investment_amount + (monthly_investment_amount * num_months)
        data['FullSumValue'] = (data[close_col] / initial_price_full) * total_investment_full
        final_value_full = data['FullSumValue'].iloc[-1]
        return_full_pct = ((final_value_full / total_investment_full) - 1) * 100 if total_investment_full > 0 else 0

        # --- Scenario 2: Invest Part Monthly ---
        investment_dates = pd.to_datetime(data.resample("MS").first().index)
        investment_dates = investment_dates[investment_dates >= pd.to_datetime(investment_date)]
        investment_schedule = {date.strftime("%Y-%m-%d"): monthly_investment_amount for date in investment_dates}
        investment_schedule[investment_date.strftime("%Y-%m-%d")] = investment_schedule.get(investment_date.strftime("%Y-%m-%d"), 0) + initial_investment_amount

        portfolio_value_monthly = pd.Series(index=data.index, dtype=float)
        total_shares_monthly = 0
        total_invested_monthly = 0

        for date, price in data[close_col].items():
            investment_on_date = investment_schedule.get(date.strftime("%Y-%m-%d"), 0)
            if investment_on_date > 0:
                shares_bought = investment_on_date / price
                total_shares_monthly += shares_bought
                total_invested_monthly += investment_on_date
            portfolio_value_monthly[date] = total_shares_monthly * price

        portfolio_df_monthly = pd.DataFrame({'Value': portfolio_value_monthly})
        portfolio_df_monthly = portfolio_df_monthly.dropna()
        final_value_monthly = portfolio_df_monthly['Value'].iloc[-1] if not portfolio_df_monthly.empty else 0
        return_monthly_pct = ((final_value_monthly / total_invested_monthly) - 1) * 100 if total_invested_monthly > 0 else 0

        # --- Comparison Chart ---
        comparison_df = pd.DataFrame({
            'Date': data.index,
            'Invest Full Sum Initially': data['FullSumValue'],
            'Invest Part Monthly': portfolio_df_monthly['Value'].reindex(data.index, method='pad')
        })

        fig_comparison = px.line(comparison_df, x='Date', y=['Invest Full Sum Initially', 'Invest Part Monthly'],
                               title="Comparison: Investing Full Sum Initially vs. Part Monthly")
        fig_comparison.update_yaxes(title_text="Portfolio Value ($)")
        st.plotly_chart(fig_comparison, use_container_width=True)

        # --- Comparison Summary ---
        st.subheader("💰 Comparison Summary")
        col1, col2, col3 = st.columns(3)
        col1.metric("Final Value (Full Sum)", f"${final_value_full:,.2f}")
        col2.metric("Return (Full Sum)", f"{return_full_pct:.2f}%")
        col3.metric("Total Invested (Full Sum)", f"${total_investment_full:,.2f}")

        col4, col5, col6 = st.columns(3)
        col4.metric("Final Value (Part Monthly)", f"${final_value_monthly:,.2f}")
        col5.metric("Return (Part Monthly)", f"{return_monthly_pct:.2f}%")
        col6.metric("Total Invested (Part Monthly)", f"${total_invested_monthly:,.2f}")

else:
    st.info("Please select a stock to begin.")
