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
TARGETPRICE_1 = 0.001753

# Define code parameters
COUNTERMAX = 20


# Starting the script

symbol = ASSET + BASE
# Create client connection to binance by using the User keys
client = Client(api_key, api_secret)

# Following few lines is to sync system time to binance server time - needed to bypass binance API security for synced times
gt = client.get_server_time()
tt=time.gmtime(int((gt["serverTime"])/1000))
win32api.SetSystemTime(tt[0],tt[1],0,tt[2],tt[3],tt[4],tt[5],0)

# Requesting ASSET balance and priting them
print("--- Binance "+ASSET+" ---")
balance = client.get_asset_balance(asset = ASSET)
free_balance = balance['free']
locked_balance = balance['locked']
total_balance = free_balance + locked_balance
print("Free balance: "+str(free_balance))
print("Locked balance: "+str(locked_balance))
print("Total balance: "+str(total_balance))

print("--- Starting price monitoring ---")

# Run a continuous loop to check on price and execute (something)
#while total_balance != 0:

# Create a counter to control infinite while loops
counter = 0

while counter < COUNTERMAX:

    counter += 1
    print("...#"+str(counter))

    # Get all prices using exchange package
    prices_binanceclient = client.get_all_tickers()

    # Defining an empty dict for prices
    prices={}

    # Converting binance response into the prices dict
    for asset in prices_binanceclient:
        prices[asset['symbol']]=asset['price']

    price = float(prices[symbol])

    msg = "current price: "+str(price)

    # If price reaches target, place market sell order
    if price >= TARGETPRICE_1 :
        print(msg+'-> SELL!')
        # Currently limit buy for test purposes
        # order = client.order_limit_buy(
        #     symbol = symbol,
        #     quantity = 10000,
        #     price = '0.000100'
        # )
    else :
        print(msg+'-> HODL!')


