from binance.client import Client
from api_keys import api_key_1
import time
import win32api

# Define API key and secret as variables
api_key = api_key_1['api_key']
api_secret = api_key_1['api_secret']

# Define trade parameters
ASSET = 'BNB'
BASE = 'BTC'
TARGETPRICE_1 = 0.0015500
QUANTITY = 45

# Define the maximum number of cycles for the code to run
COUNTERMAX = 20


# Starting the script

# Derive symbol from 'ASSET' and 'BASE'
symbol = ASSET + BASE

# Create client connection to exchange by using API keys
client = Client(api_key, api_secret)

# Sync system time to exchange server time - needed to bypass exchange API security requirements for synced times
gt = client.get_server_time()
tt = time.gmtime(int((gt["serverTime"])/1000))
win32api.SetSystemTime(tt[0],tt[1],0,tt[2],tt[3],tt[4],tt[5],0)

# Query ASSET balance
print(ASSET+" on Binance")
balance = client.get_asset_balance(asset = ASSET)
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

while counter < COUNTERMAX:

    counter += 1
    print("")
    print("Running cycle #"+str(counter))

    # Get all prices using exchange package
    prices_client = client.get_all_tickers()

    # Define an empty dictionary for prices
    prices = {}

    # Convert exchange response into the prices dictionary
    for asset in prices_client:
        prices[asset['symbol']]=asset['price']

    # Query price for symbol
    price = float(prices[symbol])
    msg = "Current price: "+str(price)

    # If price reaches target, place market sell order
    if price >= TARGETPRICE_1 :

        print(msg+' -> SELL!')

        # Get open orders for symbol
        orders = client.get_open_orders(symbol = symbol)

        # Cancel open orders for symbol
        for order in orders:
            print("")
            print("Cancelling existing orders:")
            print(order['orderId'])
            result = client.cancel_order(
                symbol = symbol,
                orderId = order['orderId']
            )

        # Place market sell order
        "Egyelőre limit buy order teszt célokból"
        "QUANTITY-t majd lehet le kell cserélni total_balance-ra"
        print("")
        print("Placing market sell order")
        order = client.order_limit_buy(
            symbol = symbol,
            quantity = QUANTITY,
            price = '0.0002100'
        )

        print("")
        print("Order placed, finishing process")
        break

    else :
        print(msg+' -> HODL!')
