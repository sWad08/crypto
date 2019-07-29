from binance.client import Client
from api_keys import api_key_1
import pandas as pd
import numpy as np
import datetime

from calcs import moving_avg_signal

import matplotlib.pyplot as plt
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

reinv_ratio = 0.98
trade_fee_rate = 0.00075
slippage_factor = 0.05
end_date = None #pd.Timestamp('2019-02-01') #15000
end = -1

window_list = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55]

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
#window_short = [10]
#window_long = [20]

# Define start date for backtesting
start_date = pd.Timestamp('2017-10-01')

# Set initial capital for backtesting
initial_capital = float(3000.0)
initial_asset_qty = 0.0

TRIGGER = 'trigger'
REINV_VALUE = 'reinv_value'
SLIPPAGE_RANGE = 'slippage_range'
SLIPPAGE_FACTOR = 'slippage_factor'
SLIPPAGE = 'slippage'
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
ASSET_PRICE_HIGH = 'asset_price_high'
ASSET_PRICE_LOW = 'asset_price_low'
ASSET_PRICE_CLOSE = 'asset_price_close'

# # Define API key and secret as variables
# api_key = api_key_1['api_key']
# api_secret = api_key_1['api_secret']
#
# # Create client for exchange package
# client = Client(api_key, api_secret)
#
# # Get historical data from exchange
# klines = client.get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_1HOUR, "17 Aug, 2017", "1 Jul, 2019")
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

if end_date is not None:
    inputs = inputs.loc[:end_date]
elif end is not None:
    inputs = inputs.iloc[:end]

# Initialize a DataFrame for signals
signals = pd.DataFrame(index=inputs.index)

# Load price data from inputs
signals[ASSET_PRICE_OPEN] = inputs['Open']
signals[ASSET_PRICE_HIGH] = inputs['High']
signals[ASSET_PRICE_LOW] = inputs['Low']
signals[ASSET_PRICE_CLOSE] = inputs['Close']

for i in range(len(window_short)):

    # Calculate moving averages based on windows defined earlier
    moving_avg_signal(signals,window_short[i],window_long[i],col_name_override=TRIGGER + '_' + str(i))

# Calculate asset quantity for benchmark: buying and holding as many units of asset as the initial capital enables
initial_price = signals[ASSET_PRICE_OPEN].at[start_date]
bm_qty = initial_capital / initial_price

# Remove rows before start date
signals = signals[start_date:]
print("Working on " + str(len(signals.index)) + " number of periods")
starttime = datetime.datetime.now()

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
    signal_df[ASSET_PRICE_HIGH] = signals[ASSET_PRICE_HIGH]
    signal_df[ASSET_PRICE_LOW] = signals[ASSET_PRICE_LOW]
    signal_df[ASSET_PRICE_CLOSE] = signals[ASSET_PRICE_CLOSE]
    signal_df[TRIGGER] = signals[TRIGGER + '_' + str(i)]
    # Preload columns necessary for portfolio value calculation
    signal_df[SLIPPAGE_RANGE] = np.nan
    signal_df[SLIPPAGE_FACTOR] = slippage_factor
    signal_df[SLIPPAGE] = np.nan
    signal_df[TRADE_PRICE] = np.nan
    signal_df[REINV_VALUE] = np.nan
    signal_df[TRADE_QTY] = np.nan
    signal_df[TRADE_VALUE_NET] = np.nan
    signal_df[TRADE_FEE] = np.nan
    signal_df[TRADE_VALUE_GROSS] = np.nan
    signal_df[ASSET_QTY_OPEN] = np.nan
    signal_df[ASSET_QTY_CLOSE] = np.nan
    signal_df[ASSET_VALUE_OPEN] = np.nan
    signal_df[ASSET_VALUE_CLOSE] = np.nan
    signal_df[CASH_VALUE_OPEN] = np.nan
    signal_df[CASH_VALUE_CLOSE] = np.nan
    signal_df[PORTF_VALUE_OPEN] = np.nan
    signal_df[PORTF_VALUE_CLOSE] = np.nan

    signal_df[ASSET_QTY_OPEN][0] = initial_asset_qty
    signal_df[ASSET_QTY_CLOSE][0] = initial_asset_qty
    signal_df[CASH_VALUE_OPEN][0] = initial_capital
    signal_df[CASH_VALUE_CLOSE][0] = initial_capital
    signal_df[PORTF_VALUE_OPEN][0] = initial_capital
    signal_df[PORTF_VALUE_CLOSE][0] = initial_capital

    signals_list.append(signal_df)

signals_names = tuple(['signals_' + str(x) for x in range(len(signals_list))])
multiindex_df = pd.concat(signals_list, keys=signals_names)

# Iterate over specific parts of the DataFrame to carry out specific calculations
# (e.g.: open values are equal to the close values of the previous period)

# Create lists to distinguish between open and close figures
open_list = [ASSET_QTY_OPEN, ASSET_VALUE_OPEN, CASH_VALUE_OPEN, PORTF_VALUE_OPEN]
close_list = [ASSET_QTY_CLOSE, ASSET_VALUE_CLOSE, CASH_VALUE_CLOSE, PORTF_VALUE_CLOSE]

# Calculate the combined trigger dates list (any date when any of the signals triggered)
signals['trigger_SUM'] = 0.0
for i in range(len(window_short)):
    signals['trigger_SUM'] = signals['trigger_SUM'] + signals['trigger_' + str(i)].abs()
trigger_dates = signals[signals['trigger_SUM'] != 0.0].index
print("Getting ready to process a total of " + str(len(trigger_dates)) + " trigger dates")

counter = 0
prev_trigger_date = signals.index[0]
for period in trigger_dates:

    counter += 1

    # Read values from sub-DataFrame (and assign them to variables)
    # by converting the numpy array from .values[0] into a list
    signal_prev_period_pairs = [tuple([x, prev_trigger_date]) for x in signals_names]
    signal_period_pairs = [tuple([x, period]) for x in signals_names]
    asset_qty_open, asset_value_open, cash_value_open, portf_value_open = list(multiindex_df.loc[signal_prev_period_pairs, close_list].values.T)

    asset_price_open, asset_price_high, asset_price_low, asset_price_close, trigger, slippage_factor = \
        list(multiindex_df.loc[signal_period_pairs, [ASSET_PRICE_OPEN, ASSET_PRICE_HIGH, ASSET_PRICE_LOW, ASSET_PRICE_CLOSE, 'trigger', SLIPPAGE_FACTOR]].values.T)

    reinv_value = reinv_ratio * cash_value_open

    slippage_range = np.ndarray(len(trigger))
    slippage = np.ndarray(len(trigger))
    trade_qty = np.ndarray(len(trigger))
    trade_price = np.ndarray(len(trigger))

    for i in range(len(trigger)):
        if np.isnan(trigger[i]):
            slippage_range[i] = 0.0
            slippage[i] = 0.0
            trade_qty[i] = 0.0
            trade_price[i] = 0.0
        elif trigger[i] == 1.0:
            slippage_range[i] = asset_price_high[i] - asset_price_open[i]
            slippage[i] = slippage_range[i] * slippage_factor[i]
            trade_qty[i] = reinv_value[i] / asset_price_open[i]
            trade_price[i] = asset_price_open[i] + slippage[i]
        elif trigger[i] == -1.0:
            slippage_range[i] = asset_price_open[i] - asset_price_low[i]
            slippage[i] = -slippage_range[i] * slippage_factor[i]
            trade_qty[i] = asset_qty_open[i] * trigger[i]
            trade_price[i] = asset_price_open[i] + slippage[i]
        else:
            slippage_range[i] = 0.0
            slippage[i] = 0.0
            trade_qty[i] = 0.0
            trade_price[i] = 0.0

    trade_value_net = trade_price * trade_qty
    trade_fee = trade_fee_rate * trade_value_net
    trade_value_gross = trade_value_net + trade_fee
    asset_qty_close = asset_qty_open + trade_qty
    asset_value_close = asset_qty_close * asset_price_close
    cash_value_close = cash_value_open - trade_value_gross
    portf_value_close = asset_value_close + cash_value_close

    # Assign values into DataFrame (.loc is a sub DataFrame) via np.array (from a list)
    multiindex_df.loc[signal_period_pairs, open_list + close_list + [REINV_VALUE] + [SLIPPAGE_RANGE] + [SLIPPAGE] + [TRADE_PRICE] + [TRADE_QTY] + [TRADE_VALUE_NET] + [TRADE_FEE] + [TRADE_VALUE_GROSS]] = \
        np.array([asset_qty_open, asset_value_open, cash_value_open, portf_value_open,
                  asset_qty_close, asset_value_close, cash_value_close, portf_value_close,
                  reinv_value, slippage_range, slippage, trade_price, trade_qty, trade_value_net, trade_fee, trade_value_gross]).T
    prev_trigger_date = period
    if counter % 100 == 0:
        print("Processed " + str(counter) + " trigger dates")


# finally fill in the missing gaps
multiindex_df[ASSET_QTY_CLOSE].fillna(method='ffill',inplace=True)
multiindex_df[CASH_VALUE_CLOSE].fillna(method='ffill',inplace=True)
multiindex_df[ASSET_VALUE_CLOSE] = multiindex_df[ASSET_QTY_CLOSE] * multiindex_df[ASSET_PRICE_CLOSE]
multiindex_df[PORTF_VALUE_CLOSE] = multiindex_df[ASSET_VALUE_CLOSE] + multiindex_df[CASH_VALUE_CLOSE]
try:
    multiindex_df.to_csv('signals.csv')
except:
    print("Can't use signals.csv file for saving...")

portf_value_close = multiindex_df.loc[signal_period_pairs,PORTF_VALUE_CLOSE].values.T
top_3_idx = np.argsort(portf_value_close)[-3:]

last_period = signals.index[-1]
print("\nBenchmark value: " + str(signals['bm_value_close'].loc[last_period]))
# print("Portfolio value: " + str(signals['portf_value_close'].iloc[counter-1]))

colors = ['r', 'g', 'b']

for i in range(len(top_3_idx)):

    idx = top_3_idx[i]

    print("Portfolio value MA(" + str(window_short[idx]) + "," + str(window_long[idx]) + "): " + str(multiindex_df.loc['signals_' + str(idx),].portf_value_close[-1]))

    plt.plot(multiindex_df.loc['signals_' + str(idx),].index,
             multiindex_df.loc['signals_' + str(idx),].portf_value_close,
             color = colors[i],
             label="Portfolio value MA(" + str(window_short[idx]) + "," + str(window_long[idx]) + ")")

endtime = datetime.datetime.now()
runtime = endtime - starttime
print("Runtime: " + str(runtime))
plt.plot(signals.index, signals.bm_value_close, color='black', label='Benchmark value')
plt.xlabel('Time')
plt.ylabel('USD')
plt.legend()
plt.show()
