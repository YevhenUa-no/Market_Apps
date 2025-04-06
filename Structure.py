import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np

# Title and Sidebar Setup
st.title("📊 Stock Portfolio Analysis")

# Sidebar Inputs
ticker_symbol = st.sidebar.text_input("Enter Stock Ticker (e.g. AAPL)", "AAPL")
start_date = st.sidebar.date_input("Start Date", datetime(2010, 1, 1))
end_date = st.sidebar.date_input("End Date", datetime.today())

# Load Data
data = yf.download(ticker_symbol, start=start_date, end=end_date)

# Close Column Selection
close_col = 'Close'

# Display Stock Data
st.subheader(f"Stock Data for {ticker_symbol}")
st.dataframe(data.tail())

# 📈 Closing Price Plot
st.subheader(f"📉 {ticker_symbol} Closing Price Over Time")
fig = px.line(data, x=data.index, y=close_col, title=f"{ticker_symbol} Closing Price")
fig.update_yaxes(title_text="Price ($)")
st.plotly_chart(fig, use_container_width=True)

# 📆 Monthly Investment Growth Over Time
st.subheader("📆 Monthly Investment Growth Over Time")

# Monthly Investment Input
monthly_amount = st.number_input("Enter Monthly Investment Amount ($)", value=1000, step=100)

# Get list of monthly dates to invest
monthly_dates = pd.date_range(start=start_date, end=end_date, freq='MS').date

# Build investment over time
investment_tracker = pd.DataFrame(index=data.index)
investment_tracker['Total Shares'] = 0
investment_tracker['Invested Amount'] = 0
investment_tracker['Value'] = 0

total_shares = 0
total_invested = 0
markers = []

for dt in monthly_dates:
    if dt in data.index:
        buy_price = data.loc[dt, close_col]
        shares_bought = monthly_amount / buy_price
        total_shares += shares_bought
        total_invested += monthly_amount
        markers.append(dt)
    investment_tracker.loc[dt:, 'Total Shares'] = total_shares
    investment_tracker.loc[dt:, 'Invested Amount'] = total_invested
    investment_tracker['Value'] = investment_tracker['Total Shares'] * data[close_col]

# Plot total investment value over time
fig_dca = px.line(
    investment_tracker,
    x=investment_tracker.index,
    y='Value',
    title="Total Value of Monthly Investments Over Time"
)

# Add markers for each investment date
fig_dca.add_scatter(
    x=markers,
    y=investment_tracker.loc[markers, 'Value'],
    mode='markers',
    marker=dict(color='red', size=8, symbol='circle'),
    name='Investment Days'
)

fig_dca.update_yaxes(title_text="Total Portfolio Value ($)")
st.plotly_chart(fig_dca, use_container_width=True)

# Summary of monthly investing
total_current_value = investment_tracker['Value'].iloc[-1]
st.markdown(f"**Total Invested via Monthly Contributions:** ${total_invested:,.2f}")
st.markdown(f"**Current Value of Monthly Investments:** ${total_current_value:,.2f}")
st.markdown(f"**Total Gain:** ${total_current_value - total_invested:,.2f} ({((total_current_value / total_invested - 1)*100):.2f}%)")

# 📉 Historical Performance
st.subheader(f"📈 {ticker_symbol} Performance Analysis")
st.markdown("This section compares the performance of your investments to the stock's historical performance.")

# Calculate Returns on Investment
returns = data['Close'].pct_change()
investment_returns = investment_tracker['Value'].pct_change().fillna(0)

# Create a DataFrame for comparison
comparison_df = pd.DataFrame({
    'Date': data.index,
    'Stock Return': returns,
    'Investment Return': investment_returns
})

# Plot performance comparison
fig_comparison = px.line(comparison_df, x='Date', y=['Stock Return', 'Investment Return'], title="Stock vs. Investment Return")
fig_comparison.update_yaxes(title_text="Return (%)")
st.plotly_chart(fig_comparison, use_container_width=True)

# 📈 Performance Measures for Stock vs Investment
st.subheader("📊 Performance Measures")

# Annualized Returns for Stock vs Investment
annualized_stock_return = (1 + returns.mean())**252 - 1
annualized_investment_return = (1 + investment_returns.mean())**252 - 1

# Volatility (Standard Deviation)
stock_volatility = returns.std() * np.sqrt(252)
investment_volatility = investment_returns.std() * np.sqrt(252)

# Sharpe Ratio
risk_free_rate = 0.02  # Assume a 2% risk-free rate
stock_sharpe = (annualized_stock_return - risk_free_rate) / stock_volatility
investment_sharpe = (annualized_investment_return - risk_free_rate) / investment_volatility

# Display Performance Measures
st.markdown(f"**Stock Annualized Return:** {annualized_stock_return * 100:.2f}%")
st.markdown(f"**Investment Annualized Return:** {annualized_investment_return * 100:.2f}%")
st.markdown(f"**Stock Volatility (Annualized):** {stock_volatility * 100:.2f}%")
st.markdown(f"**Investment Volatility (Annualized):** {investment_volatility * 100:.2f}%")
st.markdown(f"**Stock Sharpe Ratio:** {stock_sharpe:.2f}")
st.markdown(f"**Investment Sharpe Ratio:** {investment_sharpe:.2f}")

# Display Option to Show Data Table
if st.checkbox("Show Investment Data Table"):
    st.subheader("Investment Tracker Data")
    st.dataframe(investment_tracker.tail())
