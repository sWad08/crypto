from binance.client import Client
from api_keys import api_key_1
import pandas as pd
import numpy as np
import datetime

from calcs import moving_avg_signal

import matplotlib.pyplot as plt
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

# Define label name constants
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

# Set initial capital for backtesting
initial_capital = float(3000.0)
initial_asset_qty = 0.0
reinv_ratio = 0.98
trade_fee_rate = 0.00075
slippage_factor = 0.05

# Define start date for backtesting
start_date = pd.Timestamp('2017-10-01') #pd.Timestamp('2017-09-01')
# Define end date for backtesting
end_date = pd.Timestamp('2019-07-01') #15000 None
end = None #-1

# define list of windows we would want to create a combination from
window_list = [5,10,20,40]#list(range(1, 55)) #[1,2,5,8,13,21,34,55]#

window_short = []
window_long = []

for short in window_list:
    for long in window_list:
        if short < long:
            window_short.append(short)
            window_long.append(long)


# Define short and long windows for moving average calculation (to override previous combinations if needed)
#window_short = [10]
#window_long = [20]

# # Define API key and secret as variables
# api_key = api_key_1['api_key']
# api_secret = api_key_1['api_secret']
#
# # Create client for exchange package
# client = Client(api_key, api_secret)
#
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

if end_date is not None:
    inputs = inputs.loc[:end_date]
elif end is not None:
    inputs = inputs.iloc[:end]

# Initialize a DataFrame for signals
signals = pd.DataFrame(index=inputs.index)

# Load open and close prices from inputs
signals[ASSET_PRICE_OPEN] = inputs['Open']
signals[ASSET_PRICE_HIGH] = inputs['High']
signals[ASSET_PRICE_LOW] = inputs['Low']
signals[ASSET_PRICE_CLOSE] = inputs['Close']

print("Working on " + str(len(window_short)) + " triggers...")
trigger_list = []
for i in range(len(window_short)):

    # Calculate moving averages based on windows defined earlier and adding it into a list of triggers (no need to store
    # in the dataframe itself)
    trigger_list.append(moving_avg_signal(signals,window_short[i],window_long[i],save_in_df=False))

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

# setup some constant names in list for later optimized access
open_list = [ASSET_QTY_OPEN, ASSET_VALUE_OPEN, CASH_VALUE_OPEN, PORTF_VALUE_OPEN]
close_list = [ASSET_QTY_CLOSE, ASSET_VALUE_CLOSE, CASH_VALUE_CLOSE, PORTF_VALUE_CLOSE]

# initiating final combined dataframe
signals_list = list()
multiindex_df = pd.DataFrame()
last_portf_value = []

for i in range(len(window_short)):
    signal_df = pd.DataFrame()
    signal_df['bm_value_close'] = signals['bm_value_close']
    signal_df[ASSET_PRICE_OPEN] = signals[ASSET_PRICE_OPEN]
    signal_df[ASSET_PRICE_HIGH] = signals[ASSET_PRICE_HIGH]
    signal_df[ASSET_PRICE_LOW] = signals[ASSET_PRICE_LOW]
    signal_df[ASSET_PRICE_CLOSE] = signals[ASSET_PRICE_CLOSE]
    signal_df[TRIGGER] = trigger_list[i]
    # Preload columns necessary for portfolio value calculation
    signal_df[SLIPPAGE_RANGE] = np.nan
    signal_df[SLIPPAGE_FACTOR] = slippage_factor
    signal_df[SLIPPAGE] = np.nan
    signal_df[TRADE_PRICE] = signal_df[ASSET_PRICE_OPEN]
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

    # NEXT STEP: iterate over specific parts of the DataFrame to carry out specific calculations
    # (e.g.: open values are equal to the close values of the previous period)

    triggered_df = signal_df[signal_df[TRIGGER] != 0.0]

    signal_print_name = "signal_" + str(i) + " - MA(" + str(window_short[i]) + "," + str(window_long[i]) + ")"
    print("Processing " + signal_print_name + " : Total of " + str(len(triggered_df.index)) + " trigger dates...")

    # taking the working dataset into a numpy matrix (set of arrays/vectors)
    # order is important as we will refer to them by that
    field_list = [TRIGGER,          ASSET_PRICE_OPEN,   ASSET_PRICE_HIGH,   ASSET_PRICE_LOW,    ASSET_PRICE_CLOSE,
                  SLIPPAGE_RANGE,   SLIPPAGE,           TRADE_PRICE,        REINV_VALUE,        TRADE_QTY,
                  TRADE_VALUE_NET,  TRADE_VALUE_GROSS,  TRADE_FEE,          ASSET_QTY_OPEN,     ASSET_VALUE_OPEN,
                  CASH_VALUE_OPEN,  PORTF_VALUE_OPEN,   ASSET_QTY_CLOSE,    ASSET_VALUE_CLOSE,  CASH_VALUE_CLOSE,
                  PORTF_VALUE_CLOSE]

    data = triggered_df[field_list].values
    starting_open_values = signal_df[close_list].iloc[0].values

    counter = 0
    for i in range(0,len(triggered_df.index)):

        counter += 1

        # Read values from sub-DataFrame (and assign them to variables)
        # by converting the numpy array from .values[0] into a list
        if i == 0:
            asset_qty_open, asset_value_open, cash_value_open, portf_value_open = list(starting_open_values)
        else:
            asset_qty_open, asset_value_open, cash_value_open, portf_value_open = list(data[i-1,17:21]) #take the close list

        trigger, asset_price_open, asset_price_high, asset_price_low, asset_price_close = list(data[i,0:5])

        reinv_value = reinv_ratio * cash_value_open

        if np.isnan(trigger):
            slippage_range = 0.0
            slippage = 0.0
            trade_qty = 0.0
            trade_price = 0.0
        elif trigger == 1.0:
            slippage_range = asset_price_high - asset_price_open
            slippage = slippage_range * slippage_factor
            trade_qty = reinv_value / asset_price_open
            trade_price = asset_price_open + slippage
        elif trigger == -1.0:
            slippage_range = asset_price_open - asset_price_low
            slippage = -slippage_range * slippage_factor
            trade_qty = asset_qty_open * trigger
            trade_price = asset_price_open + slippage
        else:
            slippage_range = 0.0
            slippage = 0.0
            trade_qty = 0.0
            trade_price = 0.0

        trade_value_net = trade_price * trade_qty
        trade_fee = trade_fee_rate * trade_value_net
        trade_value_gross = trade_value_net + trade_fee
        asset_qty_close = asset_qty_open + trade_qty
        asset_value_close = asset_qty_close * asset_price_close
        cash_value_close = cash_value_open - trade_value_gross
        portf_value_close = asset_value_close + cash_value_close

        # Assign values into the data MATRIX
        data[i,5:21] = np.array([slippage_range,
                                 slippage,
                                 trade_price,
                                 reinv_value,
                                 trade_qty,
                                 trade_value_net,
                                 trade_value_gross,
                                 trade_fee,
                                 asset_qty_open,
                                 asset_value_open,
                                 cash_value_open,
                                 portf_value_open,
                                 asset_qty_close,
                                 asset_value_close,
                                 cash_value_close,
                                 portf_value_close
                                 ])

    # writing back data into full dataframe
    signal_df.loc[signal_df[TRIGGER] != 0.0, field_list] = data
    signals_list.append(signal_df)
    last_portf_value.append(portf_value_close)

print("Done...combining dataframes...")
signals_names = tuple(['signals_' + str(x) for x in range(len(signals_list))])
multiindex_df = pd.concat(signals_list, keys=signals_names)

print("Done...filling regular dates...")
# finally fill in the missing gaps
multiindex_df[ASSET_QTY_CLOSE].fillna(method='ffill',inplace=True)
multiindex_df[CASH_VALUE_CLOSE].fillna(method='ffill',inplace=True)
multiindex_df[ASSET_VALUE_CLOSE] = multiindex_df[ASSET_QTY_CLOSE] * multiindex_df[ASSET_PRICE_CLOSE]
multiindex_df[PORTF_VALUE_CLOSE] = multiindex_df[ASSET_VALUE_CLOSE] + multiindex_df[CASH_VALUE_CLOSE]

print("Done...saving into csv...")
try:
    multiindex_df.to_csv('signals.csv')
except:
    print("Can't use signals.csv file for saving...")

print("Done all")
last_period = signals.index[-1]
#signal_period_pairs = [tuple([x,last_period]) for x in signals_names]
last_portf_value = np.array(last_portf_value)
top_3_idx = np.argsort(last_portf_value)[-3:]

print("\nBenchmark value: " + str(signals['bm_value_close'].loc[last_period]))

colors = ['r', 'g', 'b']

for i in range(len(top_3_idx)):

    idx = top_3_idx[i]

    print("Portfolio value MA(" + str(window_short[idx]) + "," + str(window_long[idx]) + "): " + str(last_portf_value[idx]))

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
