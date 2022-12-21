import alpaca_trade_api as tradeapi
import time
from config import API_KEY, API_SECRET, API_URL
import datetime
import threading

class fiveEMA:
    def __init__(self):
        #api data
        self.api = tradeapi.REST(API_KEY, API_SECRET, API_URL, 'v2')
        #stocks to be traded
        self.stocks = ['SPY', 'AAPL', 'MSFT', 'TSLA', 'ARKK', 'AMD', 'JPM', 'DIS', 'AMZ', 'GOOG']
        #maps holding neccessary data
        self.emas = {}
        self.closes = {}
        self.positions = {}

    #what will be run in main
    def run(self):
        #see if api connects properly
        print(self.api.get_account().status)
        self.algorithm()

    #wait for the market to open function
    def marketOpen(self):
        isOpen = self.api.get_clock().is_open
        while(not isOpen):
            clock = self.api.get_clock()
            opening = clock.next_open.replace(tzinfo=datetime.timezone.utc).timestamp()
            current = clock.timestamp.replace(tzinfo=datetime.timezone.utc).timestamp()
            toOpen = int((opening - current) / 60)
            print(str(toOpen) + " minutes till the market opens.")
            time.sleep(60)
            isOpen = self.api.get_clock().is_open

    #wait for the time to hit a 15 min break point and an extra minute for the new data to come in
    def wait(self):
        while(True):
            current_time = self.api.get_clock().timestamp.minute
            if current_time % 15 == 0:
                time.sleep(60)
                print('Ready to trade')
                break
            else:
                print('Not ready to trade yet')
                time.sleep(60)

    #calculate the 5ema of a stock
    def calculate(self):
        for stock in self.stocks:
            data = self.api.get_bars(symbol=stock,timeframe='15Min').df
            #reset timestamp index
            data = data.reset_index()
            #latest 5
            data = data.drop(data.index[-1])
            vals = data.tail().iloc[0:, 5:6]
            #last close
            last_price = vals.iloc[4, 0]
            #previous 5
            calcs = data.iloc[-10:-5, 5:6]
            #calculate the previous 5ema
            five_ema = calcs['close'].mean()
            #add close to the map
            self.closes[stock] = last_price

            #set the 5ema of each crypto
            for val in vals['close']:
                five_ema = (val*2)/6 + five_ema*(1-2/6)
            self.emas[stock] = five_ema