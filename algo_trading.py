from binance.client import Client
from api_keys import api_key_1
import pandas as pd
import numpy as np

# Define API key and secret as variables
api_key = api_key_1['api_key']
api_secret = api_key_1['api_secret']

# Create client for exchange package
client = Client(api_key, api_secret)

# # Get historical data from exchange
# klines = client.get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_1HOUR, "1 Oct, 2017", "31 Dec, 2018")
# columns = [
#     "Open time",
#     "Open",
#     "High",
#     "Low",
#     "Close",
#     "Volume",
#     "Close time",
#     "Quote asset volume",
#     "Number of trades",
#     "Taker buy base asset volume",
#     "Taker buy quote asset volume",
#     "Ignore"
#   ]
# # Create a pandas DataFrame from historical price data
# inputs = pd.DataFrame(klines, columns=columns)
#
# # Save historical data to csv so that the program does not have to query it from the exchange while backtesting
# inputs.to_csv('klines.csv')

# Load historical data for the purpose of backtesting
inputs = pd.read_csv('klines.csv', index_col=0)
inputs.set_index('Open time', inplace=True)

# Define short and long windows for moving average calculation
window_short = 13
window_long = 44

# Set initial capital for backtesting
initial_capital = float(3000.0)

# Initialize a DataFrame for signals
signals = pd.DataFrame(index=inputs.index)
signals['signal'] = 0.0

# Calculate moving averages based on windows defined earlier
signals['ma_short'] = inputs['Close'].rolling(window=window_short, min_periods=1, center=False).mean()
signals['ma_long'] = inputs['Close'].rolling(window=window_long, min_periods=1, center=False).mean()

# Create signals: 1 if bullish, 0 if bearish
signals['signal'][window_short:] = np.where(signals['ma_short'][window_short:] > signals['ma_long'][window_short:], 1.0, 0.0)  # Only for the period greater than the short MA -- IS THAT CORRECT? SHOULDN'T IT BE THE LONG MA?

# Generate triggers (change in signals along time): go long if 1, go short if -1
signals['trigger'] = signals['signal'].diff()

# Initialize a DataFrame to keep track of portfolio
portfolio = pd.DataFrame(index=signals.index).fillna(0.0)

# Simulate owning x units of asset when signal is bullish -- WE SHOULD DEFINE QUANTITY RELATIVE TO PORTFOLIO VALUE BUT THAT WOULD REQUIRE SWITCHING TO A LOOPING LOGIC
x = 0.56
portfolio['asset_qty'] = x * signals['signal']

# Calculate the change in asset quantity along time
portfolio['asset_qty_chg'] = portfolio['asset_qty'].diff()

# Calculate asset value, cash value and total portfolio value
portfolio['asset_value'] = portfolio['asset_qty'].multiply(inputs['Close'], axis=0)
portfolio['cash_value'] = initial_capital - (portfolio['asset_qty_chg'].multiply(inputs['Close'], axis=0)).cumsum()
portfolio['portf_value'] = portfolio['asset_value'] + portfolio['cash_value']

# Calculate asset quantity for benchmark: buying and holding as many units of asset as the initial capital enables
initial_price = inputs['Close'].iloc[0]
bm_qty = initial_capital / initial_price

# Add benchmark quantity and value to portfolio
portfolio['bm_qty'] = bm_qty
portfolio['bm_value'] = portfolio['bm_qty'].multiply(inputs['Close'], axis=0)

print("Portfolio value: " + str(portfolio['portf_value'].iloc[-1]))
print("Benchmark value: " + str(portfolio['bm_value'].iloc[-1]))
print("Minimum cash value: " + str(min(portfolio['cash_value'][1:])))  # Check if cash value at any point turned negative

# portfolio.to_csv('portfolio.csv')


