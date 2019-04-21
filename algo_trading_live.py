from binance.client import Client
from api_keys import api_key_1
import time
import pandas as pd

# Define API key and secret as variables
api_key = api_key_1['api_key']
api_secret = api_key_1['api_secret']

# Set reinvestment ratio
reinv_ratio = 0.98

# Initiate variable showing whether we are long (1) or neutral (0)
position = 0

# Define short and long windows for moving average calculation
window_short = 13
window_long = 44

# Create client for exchange package
client = Client(api_key, api_secret)

# Create a counter to control the running of infinite loops
counter = 0
countermax = 1000

# Create infinite loop to carry out trading strategy
while counter < countermax:

    counter += 1
    print("\nRunning cycle #" + str(counter) + " on " + time.asctime())

    # Query the latest candles to be able to calculate moving averages
    klines = client.get_klines(symbol="BTCUSDT", interval=Client.KLINE_INTERVAL_1MINUTE, limit=window_long+1)
    columns = [
        "open_time",
        "asset_price_open",
        "asset_price_high",
        "asset_price_low",
        "asset_price_close",
        "vol",
        "close_time",
        "quote_asset_vol",
        "nr_of_trades",
        "taker_buy_base_asset_vol",
        "taker_buy_quote_asset_vol",
        "ignore"
      ]

    # Convert klines into a DataFrame to calculate moving averages
    signals = pd.DataFrame(klines, columns=columns)
    signals['open_time'] = pd.to_datetime(signals['open_time'], unit='ms')
    signals.set_index('open_time', inplace=True)

    # Calculate moving averages based on windows defined earlier
    signals['ma_short'] = signals['asset_price_close'].rolling(window=window_short, min_periods=window_short, center=False).mean()
    signals['ma_long'] = signals['asset_price_close'].rolling(window=window_long, min_periods=window_long, center=False).mean()

    # Generate signals based on relative values of short MA and long MA
    if signals['ma_short'][-2] > signals['ma_long'][-2]:
        signal = 1
    else:
        signal = -1

    print("Open time: " + str(signals.index[-2]))
    print("Close price: " + str(signals['asset_price_close'][-1]))
    print("Short MA: " + str(signals['ma_short'][-1]))
    print("Long MA: " + str(signals['ma_long'][-1]))
    print("Signal: " + str(signal))
    print("Position: " + str(position))

    # Decide if an order has to be placed
    if signal == 1 and position == 0:

        print("BUY!")

        # Query USDT balance
        balance_usdt = client.get_asset_balance(asset='USDT')
        free_balance_usdt = float(balance_usdt['free'])
        print("USDT balance: " + str(free_balance_usdt))

        # Calculate trade quantity based on reinvestment ratio
        trade_qty = free_balance_usdt * reinv_ratio
        print("Trade quantity: " + str(trade_qty))

        # Update position as long
        position = 1

    elif signal == -1 and position == 1:

        print("SELL!")

        # Query BTC balance
        balance_btc = client.get_asset_balance(asset='BTC')
        free_balance_btc = float(balance_btc['free'])
        print("BTC balance: " + str(free_balance_btc))

        # Update position as neutral
        position = 0

    else:

        print("Nothing to see here!")

signals.to_csv('signals_live.csv')
