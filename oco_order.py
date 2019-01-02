#!/usr/bin/python
# -*- coding: utf-8 -*-

from binance.client import Client
from api_keys import api_key_1
import time
import win32api
import utils

# Define API key and secret as variables
api_key = api_key_1['api_key']
api_secret = api_key_1['api_secret']

# Define trade parameters in a dictionary (later this will be re-read from file for user updated config)
trade_params = {
    'ASSET': 'BNB',
    'BASE': 'BTC',
    'TARGETPRICE':    0.0017500,
    'TRADEPRICE':     0.0002100,
    'QUANTITY': 45,
}

utils.json_save(trade_params,'configs/trade_config.json')

# Define script parameters in a dictionary (later this will be re-read from file for user updated config)
script_params = {
    'COUNTERMAX': 20,
}
utils.json_save(script_params,'configs/script_config.json')


# Starting the script

# Derive symbol from 'ASSET' and 'BASE'
symbol = trade_params['ASSET'] + trade_params['BASE']

# Create client connection to exchange by using API keys
client = Client(api_key, api_secret)

# Sync system time to exchange server time - needed to bypass exchange API security requirements for synced times
gt = client.get_server_time()
tt = time.gmtime(int((gt["serverTime"])/1000))
win32api.SetSystemTime(tt[0], tt[1], 0, tt[2], tt[3], tt[4], tt[5], 0)

# Query ASSET balance
print(trade_params['ASSET']+" on Binance")
balance = client.get_asset_balance(asset=trade_params['ASSET'])
free_balance = float(balance['free'])
locked_balance = float(balance['locked'])
total_balance = free_balance + locked_balance
print("Free balance: "+str(free_balance))
print("Locked balance: "+str(locked_balance))
print("Total balance: "+str(total_balance))

# Initialize price monitoring
print("")
print("Initializing price monitoring")

# Run a continuous loop to monitor price and execute OCO order functionality if applicable
#while total_balance != 0:

# Create a counter to control infinite while loops
counter = 0

while script_params['COUNTERMAX'] != 0:

    # At each cycle we reload the config files to see if user changed anything at runtime
    trade_params = utils.json_load('configs/trade_config.json')
    script_params = utils.json_load('configs/script_config.json')

    counter += 1
    if counter > script_params['COUNTERMAX']:
        break

    print("")
    print("Running cycle #"+str(counter))

    # Get all prices using exchange package
    prices_client = client.get_all_tickers()

    # Create a so called "list comprehension" from the original client all_ticker response
    # The following basically takes all elements of prices_client if the 'symbol' key is equal to symbol
    prices_asset = [x for x in prices_client if x['symbol'] == symbol]

    # Query price from the filtered list. First element should be sufficient as we only have 1 symbol at the moment
    price = float(prices_asset[0]['price'])
    msg = "Current price: "+str(price)

    # If price reaches target, place market sell order
    if price >= trade_params['TARGETPRICE']:

        print(msg+' -> SELL!')

        # Get open orders for symbol
        orders = client.get_open_orders(symbol=symbol)

        # Cancel open orders for symbol
        for order in orders:
            print("")
            print("Cancelling existing orders:")
            print(order['orderId'])
            result = client.cancel_order(
                symbol=symbol,
                orderId=order['orderId']
            )

        # Place market sell order
        "Egyelőre limit buy order teszt célokból"
        "QUANTITY-t majd lehet le kell cserélni total_balance-ra"
        print("")
        print("Placing market sell order")
        order = client.order_limit_buy(
            symbol=symbol,
            quantity=trade_params['QUANTITY'],
            price=trade_params['TRADEPRICE'],
        )

        print("")
        print("Order placed, finishing process")
        break

    else :
        print(msg+' -> HODL!')
