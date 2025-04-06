import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="📈 Stock Investment Tracker", layout="wide")

# Title
st.title("📈 Stock Investment Dashboard")

# Sidebar: Ticker input
st.sidebar.header("Select Stock")
try:
    tickers_list = yf.Tickers("AAPL MSFT NVDA TSLA AMZN META GOOGL NFLX BA KO JPM V").tickers
    ticker_names = sorted(tickers_list.keys())
    ticker_symbol = st.sidebar.selectbox("Choose a stock", ticker_names)
except:
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
        data['FullSumValue'] = (data[close_col] / initial_price_full) * (initial_investment_amount + (monthly_investment_amount * (len(data.resample("MS").first().index[data.resample("MS").first().index >= pd.to_datetime(investment_date)]))))
        final_value_full = data['FullSumValue'].iloc[-1]

        # --- Scenario 2: Invest Part Monthly ---
        investment_dates = pd.to_datetime(data.resample("MS").first().index)
        investment_dates = investment_dates[investment_dates >= pd.to_datetime(investment_date)]
        investment_schedule = {date.strftime("%Y-%m-%d"): monthly_investment_amount for date in investment_dates}
        investment_schedule[investment_date.strftime("%Y-%m-%d")] = investment_schedule.get(investment_date.strftime("%Y-%m-%d"), 0) + initial_investment_amount

        portfolio_value_monthly = pd.Series(index=data.index, dtype=float)
        total_shares_monthly = 0

        for date, price in data[close_col].items():
            investment_on_date = investment_schedule.get(date.strftime("%Y-%m-%d"), 0)
            if investment_on_date > 0:
                shares_bought = investment_on_date / price
                total_shares_monthly += shares_bought
            portfolio_value_monthly[date] = total_shares_monthly * price

        portfolio_df_monthly = pd.DataFrame({'Value': portfolio_value_monthly})
        portfolio_df_monthly = portfolio_df_monthly.dropna()
        final_value_monthly = portfolio_df_monthly['Value'].iloc[-1] if not portfolio_df_monthly.empty else 0

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
        col1, col2 = st.columns(2)
        col1.metric("Final Value (Invest Full Sum Initially)", f"${final_value_full:,.2f}")
        col2.metric("Final Value (Invest Part Monthly)", f"${final_value_monthly:,.2f}")

        initial_total_investment = initial_investment_amount
        total_monthly_contributions = monthly_investment_amount * (len(investment_dates) - 1) if len(investment_dates) > 1 else 0
        total_invested_monthly = initial_total_investment + total_monthly_contributions

        col3, col4 = st.columns(2)
        col3.metric("Total Invested (Full Sum)", f"${initial_total_investment + total_monthly_contributions:,.2f}")
        col4.metric("Total Invested (Part Monthly)", f"${total_invested_monthly:,.2f}")

else:
    st.info("Please select a stock to begin.")
