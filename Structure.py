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

        investment_amount = st.sidebar.number_input("Lump-Sum Investment Amount ($)", min_value=100, step=100, value=1000)
        monthly_amount = st.sidebar.number_input("Monthly Investment Amount ($)", min_value=10, step=10, value=200)

        close_col = "Close"

        # Calculate single investment performance
        initial_price = data.loc[investment_date, close_col]
        data['LumpSumValue'] = (data[close_col] / initial_price) * investment_amount
        final_price = data[close_col].iloc[-1]
        final_lumpsum_value = data['LumpSumValue'].iloc[-1]

        total_return_pct = ((final_price - initial_price) / initial_price) * 100
        total_gain = final_lumpsum_value - investment_amount
        num_days = (data.index[-1] - investment_date).days
        annualized_return_pct = ((final_lumpsum_value / investment_amount) ** (365 / num_days) - 1) * 100 if num_days > 0 else 0.0

        # Lump-Sum Investment value chart
        fig_lumpsum = px.line(
            data,
            x=data.index,
            y='LumpSumValue',
            title=f"Development of ${investment_amount} Lump-Sum Investment in {ticker_symbol} Since {investment_date.date()}"
        )
        fig_lumpsum.update_yaxes(title_text="Estimated Value ($)")
        st.plotly_chart(fig_lumpsum, use_container_width=True)

        # 📊 Lump-Sum Investment Performance Summary
        st.subheader("📊 Lump-Sum Investment Performance Summary")
        col1, col2, col3 = st.columns(3)
        col1.metric("Initial Price", f"${initial_price:.2f}")
        col2.metric("Final Price", f"${final_price:.2f}")
        col3.metric("Total Return", f"{total_return_pct:.2f}%")

        col4, col5, col6 = st.columns(3)
        col4.metric("Current Value", f"${final_lumpsum_value:.2f}")
        col5.metric("Total Gain", f"${total_gain:.2f}")
        col6.metric("Annualized Return", f"{annualized_return_pct:.2f}%")

        # 📅 Total Investment Development Over Time
        st.subheader("📈 Total Investment Development Over Time")
        investment_dates = pd.to_datetime(data.resample("MS").first().index)
        investment_dates = investment_dates[investment_dates >= pd.to_datetime(investment_date)]
        investment_schedule = {date.strftime("%Y-%m-%d"): monthly_amount for date in investment_dates}
        investment_schedule[investment_date.strftime("%Y-%m-%d")] = investment_schedule.get(investment_date.strftime("%Y-%m-%d"), 0) + investment_amount

        portfolio_value = pd.Series(index=data.index, dtype=float)
        total_shares = 0
        cumulative_investment = 0

        for date, price in data[close_col].items():
            investment_on_date = investment_schedule.get(date.strftime("%Y-%m-%d"), 0)
            if investment_on_date > 0:
                shares_bought = investment_on_date / price
                total_shares += shares_bought
                cumulative_investment += investment_on_date
            portfolio_value[date] = total_shares * price

        portfolio_df = pd.DataFrame({'Value': portfolio_value, 'Investment': cumulative_investment})
        portfolio_df = portfolio_df.dropna()

        fig_total_investment = px.line(portfolio_df, x=portfolio_df.index, y='Value', title="Total Investment Value Over Time")
        fig_total_investment.update_yaxes(title_text="Total Portfolio Value ($)")

        # Mark investment days
        investment_marks = [pd.to_datetime(d) for d in investment_schedule.keys() if pd.to_datetime(d) in portfolio_df.index]
        fig_total_investment.add_scatter(x=investment_marks, y=portfolio_df.loc[investment_marks]['Value'],
                                         mode='markers', marker=dict(size=8, color='red'),
                                         name='Investment Day')

        st.plotly_chart(fig_total_investment, use_container_width=True)

        # Summary of total investing
        final_portfolio_value = portfolio_df['Value'].iloc[-1]
        total_invested_all = portfolio_df['Investment'].iloc[-1]
        total_gain_all = final_portfolio_value - total_invested_all
        total_return_pct_all = ((final_portfolio_value / total_invested_all) - 1) * 100 if total_invested_all > 0 else 0

        st.subheader("💰 Total Investment Summary (Lump-Sum + Monthly)")
        st.markdown(f"**Total Invested:** ${total_invested_all:,.2f}")
        st.markdown(f"**Current Portfolio Value:** ${final_portfolio_value:,.2f}")
        st.markdown(f"**Total Gain:** ${total_gain_all:,.2f} ({total_return_pct_all:.2f}%)")

else:
    st.info("Please select a stock to begin.")
