import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# --- Page Configuration ---
create_page = st.Page("market_tracking.py", title="Market Tracking", icon=":material/trending_up:")
pg = st.navigation([create_page])
st.set_page_config(page_title="Market Tracker", page_icon=":material/trending_up:")
pg.run()

# --- App Content ---
st.subheader("S&P 500 Data")

ticker = "^GSPC"
data = None

# Session state for period and date settings
period = st.session_state.get("period")
start_date = st.session_state.get("start_date")
end_date = st.session_state.get("end_date")
selected_time = st.session_state.get("selected_time")

if period or start_date:
    with st.spinner(f"Fetching S&P 500 data for {selected_time.lower()}..."):
        try:
            if selected_time == "Custom":
                data = yf.download(ticker, start=start_date, end=end_date)
            else:
                data = yf.download(ticker, period=period)
        except Exception as e:
            st.error(f"An error occurred while fetching data: {e}")
            data = pd.DataFrame()

    if data is not None and not data.empty:
        st.dataframe(data)

        st.subheader("S&P 500 Price Performance")
        try:
            fig_price = px.line(data, x=data.index, y="Close", title="S&P 500 Closing Price")
            st.plotly_chart(fig_price, use_container_width=True)
        except Exception as e:
            st.error(f"Chart creation error: {e}")

        # Volume Chart
        if st.checkbox("Show Volume Chart"):
            st.subheader("S&P 500 Trading Volume")
            fig_volume = px.bar(data, x=data.index, y="Volume", title="S&P 500 Trading Volume")
            st.plotly_chart(fig_volume, use_container_width=True)

        # Moving Average
        st.sidebar.header("Technical Indicators")
        if st.sidebar.checkbox("Show Moving Average"):
            ma_window = st.sidebar.slider("Moving Average Window (days)", 5, 200, 20)
            data['MA'] = data['Close'].rolling(window=ma_window).mean()
            fig_ma = px.line(data, x=data.index, y=["Close", "MA"],
                             title=f"S&P 500 Closing Price with {ma_window}-Day Moving Average")
            st.plotly_chart(fig_ma, use_container_width=True)

        # Date Range Filter
        st.sidebar.header("Date Range Filter")
        if len(data.index) > 1:
            min_date = data.index.min().date()
            max_date = data.index.max().date()
            date_range = st.sidebar.slider("Select Date Range", min_value=min_date, max_value=max_date,
                                           value=(min_date, max_date))
            filtered_data = data[(data.index.date >= date_range[0]) & (data.index.date <= date_range[1])]
            st.subheader("S&P 500 Performance (Filtered)")
            if not filtered_data.empty:
                fig_filtered = px.line(filtered_data, x=filtered_data.index, y="Close",
                                       title="S&P 500 Closing Price (Filtered)")
                st.plotly_chart(fig_filtered, use_container_width=True)
            else:
                st.info("No data available for the selected date range.")
        else:
            st.sidebar.info("Not enough data points for filtering.")
    else:
        st.info("No data available for the selected time period.")
else:
    st.info("Select a time period in the sidebar to view the S&P 500 performance.")

