import csv
screener_file = 'screener 12272018.xls'

#an intern must have formatted the xls file so lots of parsing is required
with open(screener_file, newline='') as csvfile:
    data = list(csv.reader(csvfile))
data = data[0][:30]
symbols = []
for i in range(len(data)):
    if i == 0:
        row = data[i].split("<tbody>")[1]
        symbol = row.split("</td><td>")[1].split("-")[0]
    else:
        row = data[i]
        symbol = row.split("</td><td>")[6].split("-")[0]
    symbols.append(symbol)

#imports and API keys
import alpaca_trade_api, time, sys
from getKey import *
api_key = getKey('alpaca_id.key')
api_secret = getKey('alpaca_secret.key')
APCA_API_BASE_URL=r'https://paper-api.alpaca.markets'
api = alpaca_trade_api.REST(api_key, api_secret, APCA_API_BASE_URL)

#define log function so that everything that is printed to console is also stored
clock = api.get_clock()
logFile = "logs\log " + clock.timestamp.strftime("%Y %m %d %H %M %S") + ".txt"
def log(msg):
    with open(logFile, 'a') as f:
        f.write(msg + '\n')
    print(msg)
log("The winners are: " + str(symbols))
#check if market is open
if not clock.is_open:
    log("Market not open. Exiting...")
    sys.exit(0)

#cancel all open orders
orders = api.list_orders()
if orders:
    for order in api.list_orders():
        api.cancel_order(order.id)
        log("Canceled " + str(order.symbol) + " order")

#close all open positions
log("Closing all positions")
positions = api.list_positions()
while positions:
    for position in positions:
        #market sell positions
        order = api.submit_order(position.symbol, position.qty, 'sell', 'market', 'gtc')
        log(str(position.symbol) + ": Submitted sell order")
        time_waiting_filled = 0
        while(order.status != 'filled'):
            time.sleep(1)
            time_waiting_filled += 1
            if order.status == 'canceled':
                raise Exception(position.symbol + " order canceled")
            elif order.status == 'expired':
                raise Exception(position.symbol + " order expired")
            order = api.get_order(order.id)
        log(position.symbol + ": Sell order filled")
    positions = api.list_positions()
log("All previously open positions have been closed")

#calculate quantities for each stock to be purchased
account = api.get_account()
ideal_equity_per_stock = 0.9*account.buying_power/30
prices = api.get_barset(symbols, 'minute', 1)
qtys = {}
for symbol in symbols:
    price = prices[symbol][0].c
    qtys[symbol] = round(ideal_equity_per_stock/price)

#Make sure we have the necessary buying power for purchasing in the quantities calculated
buying_power_required = 0
for symbol in symbols:
    buying_power_required += qtys[symbol]*prices[symbol][0].c
assert (buying_power_required < account.buying_power*0.975), "Not enough buying power"

#order stocks in quantities previously calculated
for symbol in symbols:
    api.submit_order(symbol, qtys[symbol], "buy", "market", "gtc")

#Make sure orders get filled
time_waiting_filled = 0
while orders:
    log(str(time_waiting_filled) + "    open orders: " + str([order.symbol for order in orders]))
    time.sleep(1)
    time_waiting_filled += 1
    orders = api.list_orders()

log("Done :)")
