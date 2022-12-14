import alpaca_trade_api as tradeapi
import pandas as pd

#API authentication keys from Alpaca dashboard
#https://app.alpaca.markets/paper/dashboard/overview
api_key = 'PKISNRCWZAZ2MSXHLXYP'
api_secret = 'Ljtng6fCX2OlUgaqWLzRroXGAlcsQwn1RSepdZXZ'
api_url = 'https://paper-api.alpaca.markets'


api = tradeapi.REST(api_key, api_secret, api_url, 'v2')
cryptos = ['BTCUSD', 'ETHUSD']

emas = {}
closes = {}

for crypto in cryptos:
    data = api.get_crypto_bars(crypto, '15Min', exchanges='CBSE').df
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

    for val in vals['close']:
        five_ema = (val*2)/6 + five_ema*(1-2/6)
  
    emas[crypto] = five_ema


for crypto, value in emas.items():
    if closes[crypto] > value:
        print('buy')
    else:
        print('sell')




