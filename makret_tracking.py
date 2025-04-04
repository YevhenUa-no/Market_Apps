import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# --- Page config ---
st.set_page_config(page_title="Market Tracker", page_icon=":chart_with_upwards_trend:")

# --- App Content ---
st.title("📈 S&P 500 Market Tracking")

ticker = "^GSPC"
data = None

# Sidebar Inputs (for standalone use)
st.sidebar.header("Time Period Settings")
selected_time = st.sidebar.selectbox("Time Frame", ["1mo", "3mo", "6mo", "YTD", "1y", "5y", "Max", "Custom"])
period = None
start_date = None
end_date = None

if selected_time == "Custom":
    start_date = st.sidebar.date_input("Start Date")
    end_date = st.sidebar.date_input("End Date")
else:
    period = selected_time

# Download and display data
if period or (start_date and end_date):
    with st.spinner("Fetching S&P 500 data..."):
        try:
            if selected_time == "Custom":
                data = yf.download(ticker, start=start_date, end=end_date)
            else:
                data = yf.download(ticker, period=period)
        except Exception as e:
            st.error(f"An error occurred while fetching data


