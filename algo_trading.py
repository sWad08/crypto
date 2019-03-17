from binance.client import Client
from api_keys import api_key_1
import pandas as pd
import numpy as np

import matplotlib.pyplot as plt


reinv_ratio = 0.98
trading_fee = 0.001
end = 500

# Define short and long windows for moving average calculation
window_short = 13
window_long = 44

# Set initial capital for backtesting
initial_capital = float(3000.0)

TRIGGER = 'trigger'
TRADE_PRICE = 'trade_price'
TRADE_QTY = 'trade_qty'
ASSET_QTY_OPEN = 'asset_qty_open'
ASSET_QTY_CLOSE = 'asset_qty_close'
ASSET_VALUE_OPEN = 'asset_value_open'
ASSET_VALUE_CLOSE = 'asset_value_close'
CASH_VALUE_OPEN = 'cash_value_open'
CASH_VALUE_CLOSE = 'cash_value_close'
PORTF_VALUE_OPEN = 'portf_value_open'
PORTF_VALUE_CLOSE = 'portf_value_close'
ASSET_PRICE_OPEN = 'asset_price_open'
ASSET_PRICE_CLOSE = 'asset_price_close'


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
inputs['Open time'] = pd.to_datetime(inputs['Open time'], unit='ms')
inputs.set_index('Open time', inplace=True)

inputs = inputs.iloc[0:end]

# Initialize a DataFrame for signals
signals = pd.DataFrame(index=inputs.index)

# Load open and close prices from inputs
signals[ASSET_PRICE_OPEN] = inputs['Open']
signals[ASSET_PRICE_CLOSE] = inputs['Close']

# Calculate moving averages based on windows defined earlier
signals['ma_short'] = signals[ASSET_PRICE_CLOSE].rolling(window=window_short, min_periods=1, center=False).mean()
signals['ma_long'] = signals[ASSET_PRICE_CLOSE].rolling(window=window_long, min_periods=1, center=False).mean()

# Create signals: 1 if bullish, 0 if bearish
signals['signal'] = 0.0  # Preload with zeroes
signals['signal'][window_short:] = np.where(signals['ma_short'][window_short:] > signals['ma_long'][window_short:], 1.0, 0.0)  # Only for the period greater than the short MA -- IS THAT CORRECT? SHOULDN'T IT BE THE LONG MA?

# Generate triggers if the signal changed in the previous period: go long if 1, go short if -1
signals[TRIGGER] = 0.0  # Preload with zeroes
signals[TRIGGER] = signals['signal'].diff().shift(1)

# Calculate asset quantity for benchmark: buying and holding as many units of asset as the initial capital enables
initial_price = signals[ASSET_PRICE_OPEN].iloc[0]
bm_qty = initial_capital / initial_price

# Add benchmark quantity and value to portfolio
signals['bm_qty'] = bm_qty
signals['bm_value_open'] = signals['bm_qty'].multiply(signals[ASSET_PRICE_OPEN])
signals['bm_value_close'] = signals['bm_qty'].multiply(signals[ASSET_PRICE_CLOSE])

# Preload columns necessary for portfolio value calculation
signals[TRADE_PRICE] = signals[ASSET_PRICE_OPEN]
signals[TRADE_QTY] = 0.0
signals[ASSET_QTY_OPEN] = 0.0
signals[ASSET_QTY_CLOSE] = 0.0
signals[ASSET_VALUE_OPEN] = 0.0
signals[ASSET_VALUE_CLOSE] = 0.0
signals[CASH_VALUE_OPEN] = 0.0
signals[CASH_VALUE_CLOSE] = 0.0
signals[PORTF_VALUE_OPEN] = 0.0
signals[PORTF_VALUE_CLOSE] = 0.0

signals[CASH_VALUE_OPEN][0] = initial_capital
signals[CASH_VALUE_CLOSE][0] = initial_capital
signals[PORTF_VALUE_OPEN][0] = initial_capital
signals[PORTF_VALUE_CLOSE][0] = initial_capital

# NEXT STEP: iterate over specific parts of the DataFrame to carry out specific calculations
# (e.g.: open values are equal to the close values of the previous period)
open_list = [ASSET_QTY_OPEN, ASSET_VALUE_OPEN, CASH_VALUE_OPEN, PORTF_VALUE_OPEN]
close_list = [ASSET_QTY_CLOSE, ASSET_VALUE_CLOSE, CASH_VALUE_CLOSE, PORTF_VALUE_CLOSE]


counter = 0
for period in signals.index[1:]:

    counter += 1

    # value read (and assigning to variables) from sub-DataFrame
    # by converting the numpy array from .values[0] into a list
    asset_qty_open, asset_value_open, cash_value_open, portf_value_open = list(signals.shift(1).loc[[period], close_list].values[0])

    asset_price_open, asset_price_close, trigger = \
        list(signals.loc[[period], [ASSET_PRICE_OPEN, ASSET_PRICE_CLOSE, 'trigger']].values[0])

    trade_price = asset_price_open

    if np.isnan(trigger):
        trade_qty = 0.0
    elif trigger == 1.0:
        trade_qty = reinv_ratio * cash_value_open / asset_price_open * (1.0 - trading_fee)
    elif trigger == -1.0:
        trade_qty = asset_qty_open * trigger
    else:
        trade_qty = 0.0

    asset_qty_close = asset_qty_open + trade_qty

    asset_value_close = asset_qty_close * asset_price_close

    cash_value_close = cash_value_open - (trade_qty * trade_price / (1.0 - trading_fee))

    portf_value_close = asset_value_close + cash_value_close

    # value assignment into DataFrame (.loc is a sub dataframe) via np.array (from a list)
    signals.loc[[period], open_list + close_list + [TRADE_QTY]] = \
        np.array([asset_qty_open, asset_value_open, cash_value_open, portf_value_open,
                  asset_qty_close, asset_value_close, cash_value_close, portf_value_close, trade_qty])

    if counter % 100 == 0:
        print("Processed " + str(counter) + " rows")

print("Portfolio value: " + str(signals['portf_value_close'].iloc[counter-1]))
print("Benchmark value: " + str(signals['bm_value_close'].iloc[counter-1]))

print(signals.describe())

plt.plot(signals.index, signals.portf_value_close,color='black',label='PortfValue')
plt.plot(signals.index, signals.bm_value_close,color='red',label='BenchmValue')
plt.xlabel('Time')
plt.ylabel('Dollar')
plt.legend()
plt.show()

# signals.to_csv('signals.csv')
