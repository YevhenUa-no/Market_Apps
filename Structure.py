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
