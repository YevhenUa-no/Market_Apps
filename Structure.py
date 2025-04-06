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
            "Select Investment Start Date (only trading days):",
            options=available_dates,
            format_func=lambda x: x.strftime("%Y-%m-%d")
        )

        investment_amount = st.sidebar.number_input("Lump-Sum Investment Amount ($)", min_value=100, step=100, value=1000)
        monthly_amount = st.sidebar.number_input("Monthly Investment Amount ($)", min_value=10, step=10, value=200)

        # Calculate single investment performance
        close_col = "Close"
        initial_price = data.loc[investment_date, close_col]
        data['Value'] = (data[close_col] / initial_price) * investment_amount
        final_price = data[close_col].iloc[-1]
        final_value = data['Value'].iloc[-1]

        total_return_pct = ((final_price - initial_price) / initial_price) * 100
        total_gain = final_value - investment_amount
        num_days = (data.index[-1] - investment_date).days
        annualized_return_pct = ((final_value / investment_amount) ** (365 / num_days) - 1) * 100 if num_days > 0 else 0.0

        # Investment value chart
        fig_investment = px.line(
            data,
            x=data.index,
            y='Value',
            title=f"Development of ${investment_amount} Investment in {ticker_symbol} Since {investment_date.date()}"
        )
        fig_investment.update_yaxes(title_text="Estimated Investment Value ($)")
        st.plotly_chart(fig_investment, use_container_width=True)

        # 📊 Investment Performance Summary
        st.subheader("📊 Investment Performance Summary")
        col1, col2, col3 = st.columns(3)
        col1.metric("Initial Price", f"${initial_price:.2f}")
        col2.metric("Final Price", f"${final_price:.2f}")
        col3.metric("Total Return", f"{total_return_pct:.2f}%")

        col4, col5, col6 = st.columns(3)
        col4.metric("Current Value", f"${final_value:.2f}")
        col5.metric("Total Gain", f"${total_gain:.2f}")
        col6.metric("Annualized Return", f"{annualized_return_pct:.2f}%")

        # 📅 Monthly Investment Performance Chart
        st.subheader("📆 Monthly Investment Comparison")

        monthly_results = []
        monthly_dates = data.resample("MS").first().index  # first trading day of each month

        for dt in monthly_dates:
            if dt in data.index:
                buy_price = data.loc[dt, close_col]
                shares_bought = monthly_amount / buy_price
                value_today = shares_bought * final_price
                monthly_results.append({
                    "Month": dt.strftime("%Y-%m"),
                    "Value Today": round(value_today, 2),
                    "Buy Price": round(buy_price, 2),
                    "Shares": round(shares_bought, 4),
                    "Investment": monthly_amount
                })

        monthly_df = pd.DataFrame(monthly_results)
        fig_monthly = px.bar(monthly_df, x="Month", y="Value Today", title="Value Today of Each Monthly Investment")
        fig_monthly.update_yaxes(title_text="Value Today ($)")
        st.plotly_chart(fig_monthly, use_container_width=True)

        # Summary of monthly investing
        total_invested = monthly_df["Investment"].sum()
        total_current_value = monthly_df["Value Today"].sum()
        st.markdown(f"**Total Invested via Monthly Contributions:** ${total_invested:,.2f}")
        st.markdown(f"**Current Value of Monthly Investments:** ${total_current_value:,.2f}")
        st.markdown(f"**Total Gain:** ${total_current_value - total_invested:,.2f} ({((total_current_value / total_invested - 1)*100):.2f}%)")

else:
    st.info("Please select a stock to begin.")

