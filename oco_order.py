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

# # Define trade parameters in a dictionary (later this will be re-read from file for user updated config)
# trade_params = {
#     '_comment': 'Trade specific configs are stored here',
#     'ASSET':        ['NEBL'],
#     'BASE':         ['BTC'],
#     'TARGETPRICE':  [0.0003580],
#     'TRADEPRICE':   [0.0002100],
#     'QUANTITY':     [3],
# }
# # Save the initial config to file (so that user can alter config at runtime)
# utils.json_save(trade_params, 'configs/trade_config.json')
#
#
# # Define script parameters in a dictionary (later this will be re-read from file for user updated config)
# script_params = {
#     '_comment': 'User countermax to limit the max number of cycles, use negative number for infinite run, use shutdown=1 to force break the loop',
#     'COUNTERMAX': 100,
#     'SHUTDOWN': 0,
# }
# # Save the initial config to file (so that user can alter config at runtime)
# utils.json_save(script_params, 'configs/script_config.json')

# Load the config files to define trade and script parameters
trade_params = utils.json_load('configs/trade_config.json')
script_params = utils.json_load('configs/script_config.json')



# Starting the script

# Derive symbol from 'ASSET' and 'BASE'
symbol = [a + b for a, b in zip(trade_params['ASSET'], trade_params['BASE'])]

# Create client connection to exchange by using API keys
client = Client(api_key, api_secret)

# Sync system time to exchange server time - needed to bypass exchange API security requirements for synced times
gt = client.get_server_time()
tt = time.gmtime(int((gt["serverTime"])/1000))
win32api.SetSystemTime(tt[0], tt[1], 0, tt[2], tt[3], tt[4], tt[5], 0)

# Query ASSET balance
for asset in trade_params['ASSET']:
    print(asset+" on Binance")
    balance = client.get_asset_balance(asset=asset)
    free_balance = float(balance['free'])
    locked_balance = float(balance['locked'])
    total_balance = free_balance + locked_balance
    print("  Free balance: "+str(free_balance))
    print("  Locked balance: "+str(locked_balance))
    print("  Total balance: "+str(total_balance))

# Initialize price monitoring
print("")
print("Initializing price monitoring for target prices: \n{}".format(zip(symbol,trade_params['TARGETPRICE'])))

# Run a continuous loop to monitor price and execute OCO order functionality if applicable
# Create a counter to be able control infinite loops
counter = 0

while counter < script_params['COUNTERMAX'] or script_params['COUNTERMAX'] < 0:

    counter += 1

    # At each cycle we reload the config files to see if user changed anything at runtime
    trade_params = utils.json_load('configs/trade_config.json')
    script_params = utils.json_load('configs/script_config.json')

    # Check if user initiated a shutdown via the config file
    if script_params['SHUTDOWN'] == 1:
        break

    print("")
    print("Running cycle #"+str(counter))

    # Get all prices using exchange package
    prices_client = client.get_all_tickers()

    # Create a so called "list comprehension" from the original client all_ticker response
    # The following basically takes all elements of prices_client if the 'symbol' key is equal to symbol
    prices_filtered = [{'price': float(x['price']), 'symbol': str(x['symbol'])} for x in prices_client if x['symbol'] in symbol]

    # Filter the above even further to check on symbols that are above their targetprice
    symbols_above_target = [str(x['symbol']) for x in prices_filtered if x['price'] >= trade_params['TARGETPRICE'][symbol.index(x['symbol'])]]
    print

    msg = "Current price(s): \n"
    for x in prices_filtered:
        msg += '  ' + x['symbol'] + ' = ' + str(x['price'])
        if x['symbol'] in symbols_above_target:
            msg += ' --->SELL!\n'
        else:
            msg += ' --->HODL!\n'

    print(msg)

    # If price reaches target, place market sell order
    for asset in symbols_above_target:

        # Get open orders for symbol
        orders = client.get_open_orders(symbol=asset)

        # Cancel open orders for symbol
        for order in orders:
            print("")
            print("Cancelling existing orders:")
            print(order['orderId'])
            result = client.cancel_order(
                symbol=asset,
                orderId=order['orderId']
            )

        # Place market sell order
        print("")
        print("Placing market sell order")
        order = client.order_market_sell(
            symbol=asset,
            quantity=trade_params['QUANTITY'][symbol.index(asset)],
        )

        print("")
        print("Order placed, finishing process")

        # Remove the given asset from trade_params lists and overwrite config file
        # Currently asset is hard input when getting its index, has to be made dynamic
        index = trade_params['ASSET'].index('NEBL')
        trade_params['ASSET'].pop(index)
        trade_params['BASE'].pop(index)
        trade_params['TARGETPRICE'].pop(index)
        trade_params['TRADEPRICE'].pop(index)
        trade_params['QUANTITY'].pop(index)
        utils.json_save(trade_params, 'configs/trade_config.json')

        break
