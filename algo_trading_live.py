from binance.client import Client
from api_keys import api_key_1
import time
import pandas as pd

reinv_ratio = 0.98

# Define short and long windows for moving average calculation
window_short = 13
window_long = 44

# Define API key and secret as variables
api_key = api_key_1['api_key']
api_secret = api_key_1['api_secret']

# Create client for exchange package
client = Client(api_key, api_secret)

# Get historical data to be able to calculate moving averages right when the program is started
# Currently it is just dummy historical data, will have to be replaced
klines = client.get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_1HOUR, "16 Apr, 2019", "18 Apr, 2019")
columns = [
    "Open time",
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
    "Close time",
    "Quote asset volume",
    "Number of trades",
    "Taker buy base asset volume",
    "Taker buy quote asset volume",
    "Ignore"
  ]

# Initiate DataFrame that will be be updated whenever a candle is closed
signals = pd.DataFrame(klines, columns=columns)
signals['Open time'] = pd.to_datetime(signals['Open time'], unit='ms')
signals.set_index('Open time', inplace=True)
print(signals.tail())

# Create a counter to control the running of infinite loops
counter = 0
countermax = 1000

# Initiate variables that are going to be referenced and updated in the infinite loop
curr_candle = []
curr_opening_time = 0

# Create infinite loop to query closing prices
while counter < countermax:

    counter += 1

    print("\nRunning cycle #" + str(counter) + " on " + time.asctime())

    # Define variables containing the result of the previous run of the loop
    prev_candle = curr_candle
    prev_opening_time = curr_opening_time

    # Get current kline data from exchange
    curr_candle = client.get_klines(symbol="BTCUSDT", interval=Client.KLINE_INTERVAL_1MINUTE, limit=1)

    # Extract the opening time from the current candle
    curr_opening_time = curr_candle[0][0]

    # Check if the current and previous opening times are equal
    # If not then the candle has been closed during the loop
    if curr_opening_time == prev_opening_time:
        print("The candle has not been closed yet...")

    else:

        print("The candle has been closed!")

        # Convert the closed candle to a DataFrame
        prev_candle = pd.DataFrame(prev_candle, columns=columns)
        prev_candle['Open time'] = pd.to_datetime(prev_candle['Open time'], unit='ms')
        prev_candle.set_index('Open time', inplace=True)

        # Append the closed candle to the signals DataFrame
        signals = signals.append(prev_candle)

        print("Open time: " + str(signals.index[-1]))
        print("Close price: " + str(signals['Close'][-1]))

# signals.to_csv('signals_live.csv')
