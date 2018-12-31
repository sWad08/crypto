from binance.client import Client
from api_keys import api_key_1
import pandas as pd

import time
import win32api


# Define API key and secret as variables
api_key = api_key_1['api_key']
api_secret = api_key_1['api_secret']

# Define trade parameters
SYMBOL = 'BNBBTC'
ASSET = 'BNB'
TARGETPRICE_1 = 0.001753

# Define code parameters
COUNTERMAX = 2

# Create client for exchange package
client = Client(api_key, api_secret)
gt = client.get_server_time()
tt=time.gmtime(int((gt["serverTime"])/1000))
win32api.SetSystemTime(tt[0],tt[1],0,tt[2],tt[3],tt[4],tt[5],0)

# Create a counter to control infinite while loops
counter = 0

balance = client.get_asset_balance(asset = ASSET)
free_balance = balance['free']
locked_balance = balance['locked']
total_balance = free_balance + locked_balance
print("Free balance: "+str(free_balance))
print("Locked balance: "+str(locked_balance))
print("Total balance: "+str(total_balance))

# Run a continuous loop to check on price and execute (something)
#while total_balance != 0:
while 1:

    # Get all prices using exchange package
    prices = client.get_all_tickers()

    # Select price of the specific pair
    price = pd.DataFrame(prices)
    price = float(price[price['symbol'] == SYMBOL]['price'])

    print(price)

    # If price reaches target, place market sell order
    if price >= TARGETPRICE_1 :
        print('SELL!')
        # Currently limit buy for test purposes
        # order = client.order_limit_buy(
        #     symbol = symbol,
        #     quantity = 10000,
        #     price = '0.000100'
        # )
    else :
        print('HODL!')

    counter += 1
    print("counter = "+str(counter))
    if counter > COUNTERMAX:
        break
