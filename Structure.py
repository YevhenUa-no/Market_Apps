import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta

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
    data = ticker.history(period="max")  # Fetch maximum available data

    if data.empty:
        st.warning("No data available for the selected ticker.")
    else:
        data = data.dropna()
        data.index = pd.to_datetime(data.index)
        min_date = data.index.min().date()
        max_date = data.index.max().date()
        today = date.today()

        # Sidebar: Date Selection
        st.sidebar.header("Date Selection")
        date_option = st.sidebar.radio(
            "Choose a Timeframe:",
            ["Custom", "1 Year", "6 Months", "3 Months", "1 Month"],
            index=0,
        )

        if date_option == "Custom":
            start_date = st.sidebar.date_input("Investment Start Date", min_value=min_date, max_value=max_date, value=min_date)
            end_date = st.sidebar.date_input("Analysis End Date", min_value=min_date, max_value=max_date, value=today)
        elif date_option == "1 Year":
            start_date = today - timedelta(days=365)
            end_date = today
        elif date_option == "6 Months":
            start_date = today - timedelta(days=6 * 30)  # Approximate 6 months
            end_date = today
        elif date_option == "3 Months":
            start_date = today - timedelta(days=3 * 30)  # Approximate 3 months
            end_date = today
        elif date_option == "1 Month":
            start_date = today - timedelta(days=30)
            end_date = today

        if start_date > end_date:
            st.sidebar.error("Error: Investment Start Date cannot be after Analysis End Date.")
        else:
            filtered_data = data[(data.index.date >= start_date) & (data.index.date <= end_date)].copy()

            if filtered_data.empty:
                st.warning("No data available for the selected date range.")
            else:
                # Sidebar: Investment input
                st.sidebar.header("Investment Setup")
                initial_investment_amount = st.sidebar.number_input("Initial Investment Amount ($)", min_value=100, step=100, value=1000)
                monthly_investment_amount = st.sidebar.number_input("Monthly Investment Amount ($)", min_value=10, step=10, value=200)

                close_col = "Close"

                # --- Scenario 1: Invest Whole Sum Initially ---
                initial_price_full = filtered_data.loc[pd.Timestamp(start_date), close_col]
                num_months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
                total_investment_full = initial_investment_amount + (monthly_investment_amount * num_months)
                filtered_data['FullSumValue'] = (filtered_data[close_col] / initial_price_full) * total_investment_full
                final_value_full = filtered_data['FullSumValue'].iloc[-1]

                # --- Scenario 2: Invest Part Monthly ---
                investment_dates = pd.to_datetime(filtered_data.resample("MS").first().index)
                investment_dates = investment_dates[investment_dates >= pd.to_datetime(start_date)]
                investment_schedule = {date.strftime("%Y-%m-%d"): monthly_investment_amount for date in investment_dates}
                investment_schedule[start_date.strftime("%Y-%m-%d")] = investment_schedule.get(start_date.strftime("%Y-%m-%d"), 0) + initial_investment_amount

                portfolio_value_monthly = pd.Series(index=filtered_data.index, dtype=float)
                total_shares_monthly = 0

                for date, price in filtered_data[close_col].items():
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
                    'Date': filtered_data.index,
                    'Invest Full Sum Initially': filtered_data['FullSumValue'],
                    'Invest Part Monthly': portfolio_df_monthly['Value'].reindex(filtered_data.index, method='pad')
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
                num_monthly_contributions = len([d for d in investment_schedule.keys() if d != start_date.strftime("%Y-%m-%d")])
                total_invested_monthly_calc = initial_total_investment + (monthly_investment_amount * num_monthly_contributions)

                col3, col4 = st.columns(2)
                col3.metric("Total Invested (Full Sum)", f"${total_investment_full:,.2f}")
                col4.metric("Total Invested (Part Monthly)", f"${total_invested_monthly_calc:,.2f}")

else:
    st.info("Please select a stock to begin.")
