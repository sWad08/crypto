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
#     'ASSET':        ['XLM', 'SALT'],
#     'SYMBOL':         ['XLMBTC', 'SALTBTC'],
#     'TARGETPRICE':  [0.00003030, 0.00033200],
#     'QUANTITY':     [3, 400],
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

# Create client connection to exchange by using API keys
client = Client(api_key, api_secret)

# Initialize price monitoring
print("\nInitializing price monitoring...")

# Run a continuous loop to monitor price and execute OCO order functionality if applicable
# Create a counter to be able control infinite loops
counter = 0

while counter < script_params['COUNTERMAX'] or script_params['COUNTERMAX'] < 0:

    counter += 1

    print("\n" + time.asctime() + " -- Running cycle #" + str(counter) + "...")

    # At each cycle we reload the config files to see if user changed anything at runtime
    trade_params = utils.json_load('configs/trade_config.json')
    script_params = utils.json_load('configs/script_config.json')

    # Check if user initiated a shutdown via the config file
    if script_params['SHUTDOWN'] == 1:
        break

    # Sync system time to exchange server time - needed to bypass exchange API security requirements for synced times
    try:
        gt = client.get_server_time()
    except Exception as ex:
        print("ERROR with get_server_time: " + str(ex))
        continue
    tt = time.gmtime(int((gt["serverTime"])/1000))
    win32api.SetSystemTime(tt[0], tt[1], 0, tt[2], tt[3], tt[4], tt[5], 0)

    # Get all prices using exchange client
    try:
        prices_client = client.get_all_tickers()
    except Exception as ex:
        print("ERROR with get_all_tickers: " + str(ex))
        continue

    # Create a so-called "list comprehension" from the original client all_ticker response
    # The following basically takes all elements of prices_client if the 'symbol' key is included in trade_params
    prices_filtered = [{'price': float(x['price']), 'symbol': str(x['symbol'])} for x in prices_client if x['symbol'] in trade_params['SYMBOL']]

    # Filter the above even further to check on symbols that are above their targetprice
    symbols_above_target = [str(x['symbol']) for x in prices_filtered if x['price'] >= trade_params['TARGETPRICE'][trade_params['SYMBOL'].index(x['symbol'])]]

    msg = "\nPrice comparison:\n"
    for x in prices_filtered:
        msg += '  ' + x['symbol'] + ': Target price = ' + str(trade_params['TARGETPRICE'][trade_params['SYMBOL'].index(x['symbol'])]) + ", Current price = " + str(x['price'])
        if x['symbol'] in symbols_above_target:
            msg += ' ---> SELL!\n'
        else:
            msg += ' ---> HODL!\n'

    print(msg)

    # If price reaches target, try to place market sell order
    for symbol in symbols_above_target:

        # First query asset balance to check if asset is available
        print("\n"+trade_params['ASSET'][trade_params['SYMBOL'].index(symbol)]+" quantities:")
        try:
            balance = client.get_asset_balance(asset=trade_params['ASSET'][trade_params['SYMBOL'].index(symbol)])
        except Exception as ex:
            print("ERROR with get_asset_balance: " + str(ex))
            continue
        free_balance = float(balance['free'])
        locked_balance = float(balance['locked'])
        total_balance = free_balance + locked_balance
        print("  Free balance = "+str(free_balance))
        print("  Locked balance = "+str(locked_balance))
        print("  Total balance = "+str(total_balance))
        print("  Quantity to sell = "+str(trade_params['QUANTITY'][trade_params['SYMBOL'].index(symbol)]))

        # If total balance of the respective asset is zero, remove the given asset from trade_params lists and overwrite config file
        if total_balance == 0:
            print("\nTotal balance for "+trade_params['ASSET'][trade_params['SYMBOL'].index(symbol)]+" is zero, removing from price monitoring...\n")
            index = trade_params['SYMBOL'].index(symbol)
            trade_params['ASSET'].pop(index)
            trade_params['SYMBOL'].pop(index)
            trade_params['TARGETPRICE'].pop(index)
            trade_params['QUANTITY'].pop(index)
            utils.json_save(trade_params, 'configs/trade_config.json')
        else:

            # Get open orders for symbol
            try:
                orders = client.get_open_orders(symbol=symbol)
            except Exception as ex:
                print("ERROR with get_open_orders: " + str(ex))
                continue

            # Cancel open orders for symbol
            try:
                for order in orders:
                    print("\nCancelling existing orders:")
                    print(order['orderId'])
                    result = client.cancel_order(
                        symbol=symbol,
                        orderId=order['orderId']
                    )
            except Exception as ex:
                print("ERROR with cancel_order: " + str(ex))
                continue

            # Place market sell order
            print("\nPlacing market sell order")
            for i in range(1,10):
                try:
                    order = client.order_market_sell(
                        symbol=symbol,
                        quantity=min(trade_params['QUANTITY'][trade_params['SYMBOL'].index(symbol)], total_balance),
                    )
                except Exception as ex:
                    print("ERROR with order_market_sell: " + str(ex))
                    continue
                else:
                    print("  Quantity = "+str(trade_params['QUANTITY'][trade_params['SYMBOL'].index(symbol)]))

                    print("\nOrder placed, finishing process for asset(s) above target...")

                    # Remove the given asset from trade_params lists and overwrite config file
                    index = trade_params['SYMBOL'].index(symbol)
                    trade_params['ASSET'].pop(index)
                    trade_params['SYMBOL'].pop(index)
                    trade_params['TARGETPRICE'].pop(index)
                    trade_params['QUANTITY'].pop(index)
                    utils.json_save(trade_params, 'configs/trade_config.json')

                    break

            continue
