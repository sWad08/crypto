from binance.client import Client
from api_keys import api_key_1
import pandas as pd
import numpy as np

reinv_ratio = 1.0

trading_fee = 0.001

end = 100

trade_price = 'trade_price'
trade_qty = 'trade_qty'
asset_qty_open = 'asset_qty_open'
asset_qty_close = 'asset_qty_close'
asset_value_open = 'asset_value_open'
asset_value_close = 'asset_value_close'
cash_value_open = 'cash_value_open'
cash_value_close = 'cash_value_close'
portf_value_open = 'portf_value_open'
portf_value_close = 'portf_value_close'

asset_price_open = 'asset_price_open'
asset_price_close = 'asset_price_close'


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
signals['trade_price'] = signals['asset_price_open']
signals['trade_qty'] = 0.0
signals['asset_qty_open'] = 0.0
signals['asset_qty_close'] = 0.0
signals['asset_value_open'] = 0.0
signals['asset_value_close'] = 0.0
signals['cash_value_open'] = 0.0
signals['cash_value_close'] = 0.0
signals['portf_value_open'] = 0.0
signals['portf_value_close'] = 0.0

signals['cash_value_open'][0] = initial_capital
signals['cash_value_close'][0] = initial_capital
signals['portf_value_open'][0] = initial_capital
signals['portf_value_close'][0] = initial_capital

# NEXT STEP: iterate over specific parts of the DataFrame to carry out specific calculations
# (e.g.: open values are equal to the close values of the previous period)
open_list = [asset_qty_open, asset_value_open, cash_value_open, portf_value_open]
close_list = [asset_qty_close, asset_value_close, cash_value_close, portf_value_close]


counter = 0
for period in signals.index:

    if period != signals.index[0]:
        counter += 1
        #signals.loc[[period], open_list] = signals.shift(1).loc[[period], close_list]
        signals.loc[[period], asset_qty_open] = signals.shift(1).loc[[period], asset_qty_close]
        signals.loc[[period], asset_value_open] = signals.shift(1).loc[[period], asset_value_close]
        signals.loc[[period], cash_value_open] = signals.shift(1).loc[[period], cash_value_close]
        signals.loc[[period], portf_value_open] = signals.shift(1).loc[[period], portf_value_close]

        cash_open = signals.loc[[period], cash_value_open][0]
        asset_pr_open = signals.loc[[period], asset_price_open][0]
        asset_pr_close = signals.loc[[period], asset_price_close][0]
        asset_quantity_open = signals.loc[[period], asset_qty_open][0]

        trigger = signals.loc[[period], 'trigger'][0]
        trade_pr = asset_pr_open

        if np.isnan(trigger):
            trade_quantity = 0.0
        elif trigger == 1.0:
            trade_quantity = reinv_ratio * cash_open / trade_pr * (1.0 - trading_fee)
        elif trigger == -1.0:
            trade_quantity = asset_quantity_open * trigger
        else:
            trade_quantity = 0.0

        asset_quantity_close = asset_quantity_open + trade_quantity

        asset_close = asset_quantity_close * asset_pr_close

        cash_close = cash_open - (trade_quantity * trade_pr / (1.0 - trading_fee))

        portf_close = asset_close + cash_close

        signals.loc[[period], trade_qty] = trade_quantity
        signals.loc[[period], asset_qty_close] = asset_quantity_close
        signals.loc[[period], asset_value_close] = asset_close
        signals.loc[[period], cash_value_close] = cash_close
        signals.loc[[period], portf_value_close] = portf_close

        print("did " + str(counter))
        if counter == end:
            break


print("Portfolio value: " + str(signals['portf_value_close'].iloc[counter-1]))
print("Benchmark value: " + str(signals['bm_value'].iloc[counter-1]))

print(signals.iloc[0:counter].tail())

# signals.to_csv('portfolio.csv')
