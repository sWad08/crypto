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

# Load open and close prices from inputs
signals['asset_price_open'] = inputs['Open']
signals['asset_price_close'] = inputs['Close']

# Calculate moving averages based on windows defined earlier
signals['ma_short'] = signals['asset_price_close'].rolling(window=window_short, min_periods=1, center=False).mean()
signals['ma_long'] = signals['asset_price_close'].rolling(window=window_long, min_periods=1, center=False).mean()

# Create signals: 1 if bullish, 0 if bearish
signals['signal'] = 0.0  # Preload with zeroes
signals['signal'][window_short:] = np.where(signals['ma_short'][window_short:] > signals['ma_long'][window_short:], 1.0, 0.0)  # Only for the period greater than the short MA -- IS THAT CORRECT? SHOULDN'T IT BE THE LONG MA?

# Generate triggers if the signal changed in the previous period: go long if 1, go short if -1
signals['trigger'] = 0.0  # Preload with zeroes
signals['trigger'] = signals['signal'].diff().shift(1)

# Calculate asset quantity for benchmark: buying and holding as many units of asset as the initial capital enables
initial_price = signals['asset_price_open'].iloc[0]
bm_qty = initial_capital / initial_price

# Add benchmark quantity and value to portfolio
signals['bm_qty'] = bm_qty
signals['bm_value'] = signals['bm_qty'].multiply(signals['asset_price_open'])

# Preload columns necessary for portfolio value calculation
signals['order_qty'] = 0
signals['asset_qty_open'] = 0
signals['asset_qty_close'] = 0
signals['asset_value_open'] = 0
signals['asset_value_close'] = 0
signals['cash_value_open'] = initial_capital
signals['cash_value_close'] = initial_capital
signals['portf_value_open'] = initial_capital
signals['portf_value_close'] = initial_capital

# NEXT STEP: iterate over specific parts of the DataFrame to carry out specific calculations
# (e.g.: open values are equal to the close values of the previous period)

print("Portfolio value: " + str(signals['portf_value_close'].iloc[-1]))
print("Benchmark value: " + str(signals['bm_value'].iloc[-1]))

print(signals.head())

# signals.to_csv('portfolio.csv')
