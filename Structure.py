import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

# App title
st.set_page_config(page_title="Stock Dashboard", layout="wide")
st.title("📈 Stock Dashboard")

# Sidebar Inputs
st.sidebar.header("Configuration")
ticker_symbol = st.sidebar.text_input("Enter Stock Ticker", value="AAPL")
start_date = st.sidebar.date_input("Start Date", value=pd.to_datetime("2022-01-01"))
end_date = st.sidebar.date_input("End Date", value=datetime.today())

investment_date_full = st.sidebar.date_input("Investment Start Date", value=pd.to_datetime("2022-01-01"))
investment_amount = st.sidebar.number_input("Investment Amount ($)", value=1000)

# Download stock data
data = yf.download(ticker_symbol, start=start_date, end=end_date)

# Flatten columns if MultiIndex (e.g., if multiple tickers were used)
if isinstance(data.columns, pd.MultiIndex):
    data.columns = ['_'.join(col).strip() for col in data.columns.values]

# Display data
st.subheader(f"Stock Data for {ticker_symbol}")
st.dataframe(data.tail(), use_container_width=True)

# Line chart for stock price
close_col = f'Close_{ticker_symbol}' if f'Close_{ticker_symbol}' in data.columns else 'Close'
fig_price = px.line(data, x=data.index, y=close_col, title=f"{ticker_symbol} Stock Price Over Time")
fig_price.update_yaxes(title_text="Stock Price ($)")
st.plotly_chart(fig_price, use_container_width=True)

# Bar chart for volume
volume_col = f'Volume_{ticker_symbol}' if f'Volume_{ticker_symbol}' in data.columns else 'Volume'
fig_volume = px.bar(data, x=data.index, y=volume_col, title=f"{ticker_symbol} Trading Volume Over Time")
fig_volume.update_yaxes(title_text="Volume")
st.plotly_chart(fig_volume, use_container_width=True)

# Investment value development
if pd.to_datetime(investment_date_full) not in data.index:
    st.warning("Selected investment start date not in available data range. Please choose another date.")
else:
    initial_price_full = data.loc[investment_date_full, close_col]
    data['Value'] = (data[close_col] / initial_price_full) * investment_amount

    fig_investment_full = px.line(
        data,
        x=data.index,
        y='Value',
        title=f"Development of ${investment_amount} Investment in {ticker_symbol} Since {investment_date_full.strftime('%Y-%m-%d')}"
    )
    fig_investment_full.update_yaxes(title_text="Estimated Investment Value ($)")
    st.plotly_chart(fig_investment_full, use_container_width=True)

