import alpaca_trade_api as tradeapi
import pandas as pd
import time
from config import api_key, api_secret, api_url

api = tradeapi.REST(api_key, api_secret, api_url, 'v2')
cryptos = ['BTCUSD', 'ETHUSD', 'LTCUSD', 'DOGEUSD', 'AAVEUSD', 'ALGOUSD', 'SOLUSD']

while(True):
    #data structures used in program
    emas = {}
    closes = {}
    positions = {}

    for crypto in cryptos:
        data = api.get_crypto_bars(symbol=crypto, timeframe='5Min').df
        #set correct timezone
        data = data.reset_index()
        data['timestamp'] = data['timestamp'].dt.tz_convert('America/New_York')
        data = data.set_index('timestamp')
        #latest 5
        data = data.drop(data.index[-1])
        vals = data.tail().iloc[0:, 4:5]
        #last close
        last_price = vals.iloc[4, 0]
        #previous 5
        calcs = data.iloc[-10:-5, 4:5]
        five_ema = calcs['close'].mean()
        closes[crypto] = last_price

        #set the 5ema of each crypto
        for val in vals['close']:
            five_ema = (val*2)/6 + five_ema*(1-2/6)
  
        emas[crypto] = five_ema

        #get positions of each crypto
        side = ''
        try:
            qty = float(api.get_position(crypto).qty)
            side = api.get_position(crypto).side
        except Exception as exception:
            if exception.__str__() == 'position does not exist':
                qty = 0
        positions[crypto] = [qty, side]

    #no short selling for cryptos, can only hold longs
    for crypto, ema in emas.items():
        balance = float(api.get_account().equity)
        power = balance/len(cryptos) - len(api.list_positions())
        if closes[crypto] > ema:
            if positions[crypto][0] == 0:
                api.submit_order(symbol=crypto, notional=power, side='buy', type='market', time_in_force='gtc')
                print('Bought', power, 'worth of', crypto)

        else:
            if positions[crypto][1] == 'long':
                api.submit_order(symbol=crypto, qty=positions[crypto][0], side='sell', type='market', time_in_force='gtc')
                print('Sold', power, 'worth of', crypto)

    print('balance is', float(api.get_account().equity))
    time.sleep(900)






