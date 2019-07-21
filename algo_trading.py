from binance.client import Client
from api_keys import api_key_1
import pandas as pd
import numpy as np

from calcs import moving_avg_signal

import matplotlib.pyplot as plt
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

reinv_ratio = 0.98
trade_fee_rate = 0.00075
end = 15000

window_list = [1,2,5,8,13,21,34,55]

window_short = []
window_long = []

for short in window_list:
    for long in window_list:
        if short < long:
            window_short.append(short)
            window_long.append(long)

print(window_short)
print(window_long)
print()

# Define short and long windows for moving average calculation
# window_short = [10]
# window_long =  [20]

# Define start date for backtesting
start_date = pd.Timestamp('2019-01-01')

# Set initial capital for backtesting
initial_capital = float(3000.0)

TRIGGER = 'trigger'
REINV_VALUE = 'reinv_value'
TRADE_PRICE = 'trade_price'
TRADE_QTY = 'trade_qty'
TRADE_VALUE_NET = 'trade_value_net'
TRADE_FEE = 'trade_fee'
TRADE_VALUE_GROSS = 'trade_value_gross'
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
# klines = client.get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_1HOUR, "1 Dec, 2018", "1 Jul, 2019")
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

for i in range(len(window_short)):

    # Calculate moving averages based on windows defined earlier
    moving_avg_signal(signals,window_short[i],window_long[i],col_name_override=TRIGGER + '_' + str(i))

# Calculate asset quantity for benchmark: buying and holding as many units of asset as the initial capital enables
initial_price = signals[ASSET_PRICE_OPEN].at[start_date]
bm_qty = initial_capital / initial_price

# Remove rows before start date
signals = signals[start_date:]

# Add benchmark quantity and value to signals
signals['bm_qty'] = bm_qty
signals['bm_value_open'] = signals['bm_qty'].multiply(signals[ASSET_PRICE_OPEN])
signals['bm_value_close'] = signals['bm_qty'].multiply(signals[ASSET_PRICE_CLOSE])

signals_list = list()
multiindex_df = pd.DataFrame()

for i in range(len(window_short)):
    signal_df = pd.DataFrame()
    signal_df['bm_value_close'] = signals['bm_value_close']
    signal_df[ASSET_PRICE_OPEN] = signals[ASSET_PRICE_OPEN]
    signal_df[ASSET_PRICE_CLOSE] = signals[ASSET_PRICE_CLOSE]
    signal_df[TRIGGER] = signals[TRIGGER + '_' + str(i)]
    # Preload columns necessary for portfolio value calculation
    signal_df[TRADE_PRICE] = signal_df[ASSET_PRICE_OPEN]
    signal_df[REINV_VALUE] = 0.0
    signal_df[TRADE_QTY] = 0.0
    signal_df[TRADE_VALUE_NET] = 0.0
    signal_df[TRADE_FEE] = 0.0
    signal_df[TRADE_VALUE_GROSS] = 0.0
    signal_df[ASSET_QTY_OPEN] = 0.0
    signal_df[ASSET_QTY_CLOSE] = 0.0
    signal_df[ASSET_VALUE_OPEN] = 0.0
    signal_df[ASSET_VALUE_CLOSE] = 0.0
    signal_df[CASH_VALUE_OPEN] = 0.0
    signal_df[CASH_VALUE_CLOSE] = 0.0
    signal_df[PORTF_VALUE_OPEN] = 0.0
    signal_df[PORTF_VALUE_CLOSE] = 0.0

    signal_df[CASH_VALUE_OPEN][0] = initial_capital
    signal_df[CASH_VALUE_CLOSE][0] = initial_capital
    signal_df[PORTF_VALUE_OPEN][0] = initial_capital
    signal_df[PORTF_VALUE_CLOSE][0] = initial_capital

    signals_list.append(signal_df)

signals_names = tuple(['signals_' + str(x) for x in range(len(signals_list))])
multiindex_df = pd.concat(signals_list, keys=signals_names)

# NEXT STEP: iterate over specific parts of the DataFrame to carry out specific calculations
# (e.g.: open values are equal to the close values of the previous period)
open_list = [ASSET_QTY_OPEN, ASSET_VALUE_OPEN, CASH_VALUE_OPEN, PORTF_VALUE_OPEN]
close_list = [ASSET_QTY_CLOSE, ASSET_VALUE_CLOSE, CASH_VALUE_CLOSE, PORTF_VALUE_CLOSE]

counter = 0
for period in signals.index[1:]:

    counter += 1

    # Read values from sub-DataFrame (and assign them to variables)
    # by converting the numpy array from .values[0] into a list
    signal_period_pairs = [tuple([x,period]) for x in signals_names]
    asset_qty_open, asset_value_open,cash_value_open, portf_value_open = list(multiindex_df.shift(1).loc[signal_period_pairs,close_list].values.T)

    asset_price_open, asset_price_close, trigger = \
        list(multiindex_df.loc[signal_period_pairs, [ASSET_PRICE_OPEN, ASSET_PRICE_CLOSE, 'trigger']].values.T)

    trade_price = asset_price_open
    reinv_value = reinv_ratio * cash_value_open

    trade_qty = np.ndarray(len(trigger))
    for i in range(len(trigger)):
        if np.isnan(trigger[i]):
            trade_qty[i] = 0.0
        elif trigger[i] == 1.0:
            trade_qty[i] = reinv_value[i] / trade_price[i]
        elif trigger[i] == -1.0:
            trade_qty[i] = asset_qty_open[i] * trigger[i]
        else:
            trade_qty[i] = 0.0

    trade_value_net = trade_price * trade_qty
    trade_fee = trade_fee_rate * trade_value_net
    trade_value_gross = trade_value_net + trade_fee
    asset_qty_close = asset_qty_open + trade_qty
    asset_value_close = asset_qty_close * asset_price_close
    cash_value_close = cash_value_open - trade_value_gross
    portf_value_close = asset_value_close + cash_value_close

    # Assign values into DataFrame (.loc is a sub DataFrame) via np.array (from a list)
    multiindex_df.loc[signal_period_pairs, open_list + close_list + [REINV_VALUE] + [TRADE_QTY] + [TRADE_VALUE_NET] + [TRADE_FEE] + [TRADE_VALUE_GROSS]] = \
        np.array([asset_qty_open, asset_value_open, cash_value_open, portf_value_open,
                  asset_qty_close, asset_value_close, cash_value_close, portf_value_close,
                  reinv_value, trade_qty, trade_value_net, trade_fee, trade_value_gross]).T

    if counter % 100 == 0:
        print("Processed " + str(counter) + " periods")
try:
    multiindex_df.to_csv('signals.csv')
except:
    print("Can't use signals.csv file for saving...")

top_3_idx = np.argsort(portf_value_close)[-3:]

print("\nBenchmark value: " + str(signals['bm_value_close'].iloc[counter-1]))
# print("Portfolio value: " + str(signals['portf_value_close'].iloc[counter-1]))

colors = ['r', 'g', 'b']

for i in range(len(top_3_idx)):

    idx = top_3_idx[i]

    print("Portfolio value MA(" + str(window_short[idx]) + "," + str(window_long[idx]) + "): " + str(multiindex_df.loc['signals_' + str(idx),].portf_value_close[-1]))

    plt.plot(multiindex_df.loc['signals_' + str(idx),].index,
             multiindex_df.loc['signals_' + str(idx),].portf_value_close,
             color = colors[i],
             label="Portfolio value MA(" + str(window_short[idx]) + "," + str(window_long[idx]) + ")")

plt.plot(signals.index, signals.bm_value_close, color='black', label='Benchmark value')
plt.xlabel('Time')
plt.ylabel('USD')
plt.legend()
plt.show()
