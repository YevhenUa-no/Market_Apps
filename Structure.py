import streamlit as st
from datetime import datetime, timedelta

st.title("S&P 500 Performance Dashboard")
st.markdown("Get historical S&P 500 data and visualize its performance.")

# Interactive features (in sidebar)
st.sidebar.header("Time Period")
time_options = {
    "1 Day": "1d",
    "5 Days": "5d",
    "1 Month": "1mo",
    "3 Months": "3mo",
    "6 Months": "6mo",
    "1 Year": "1y",
    "2 Years": "2y",
    "5 Years": "5y",
    "10 Years": "10y",
    "Year-to-Date": "ytd",
    "Max": "max",
    "Custom": "custom",
}
selected_time = st.sidebar.selectbox("Select Time Period", list(time_options.keys()))
st.session_state.selected_time = selected_time  # Store in session state

if selected_time == "Custom":
    start_date = st.sidebar.date_input("Start Date", datetime.now().date() - timedelta(days=365))
    end_date = st.sidebar.date_input("End Date", datetime.now().date())
    if start_date > end_date:
        st.sidebar.error("Error: Start date cannot be after end date.")
        st.stop()
    st.session_state.start_date = start_date  # Store in session state
    st.session_state.end_date = end_date    # Store in session state
    st.session_state.period = None
else:
    st.session_state.period = time_options[selected_time]
    st.session_state.start_date = None
    st.session_state.end_date = None

pg = st.navigation([
    st.Page("makret_tracking.py", name="Market Tracking"),
    # Add other pages here if you have them
])
