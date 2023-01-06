import alpaca_trade_api as tradeapi
import time
from config import API_KEY, API_SECRET, API_URL
import datetime
import pandas as pd
import threading
import math

class fiveEMA:
    def __init__(self):
        #api data
        self.api = tradeapi.REST(API_KEY, API_SECRET, API_URL, 'v2')
        #stocks to be traded
        self.stocks = ['SPY', 'AAPL', 'MSFT', 'TSLA', 'ARKK', 'AMD', 'JPM', 'DIS', 'AMZN', 'GOOG']
        #info to be used
        self.emas = {}
        self.closes = {}
        self.positions = {}
        self.data = {} 
        self.count = 0

    #what will be run in main
    def run(self):
        #wait for the market to open
        if self.api.get_clock().is_open == False:
            print('Waiting for market to open')
        open = threading.Thread(target=self.marketOpen)
        open.start()
        open.join()
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
        #wait for the time to hit a 15 min break point
        while(self.api.get_clock().timestamp.minute % 15 != 0):
            print('Not ready to trade yet')
            time.sleep(60)
        print('Ready to trade')


    #collect data organized in dataframe
    def collectData(self):
        for stock in self.stocks:
            #collect yesterday's data
            start = (self.api.get_clock().next_open - pd.tseries.offsets.BDay(2)).isoformat('T')
            end = (self.api.get_clock().next_close - pd.tseries.offsets.BDay(1)).isoformat('T')
            df = self.api.get_bars(symbol=stock, timeframe='15Min', start=start, end=end).df
            df = df.reset_index()
            df['timestamp']= df['timestamp'].dt.tz_convert('America/New_York')
            df = df.set_index('timestamp')
            df = df.between_time('13:30', '15:45')
            self.data[stock] = df
            #today's data
            start = (self.api.get_clock().next_open - pd.tseries.offsets.BDay(1)).isoformat('T')
            df = self.api.get_bars(symbol=stock, timeframe='15Min', start=start).df 
            df = df.reset_index()
            df['timestamp'] = df['timestamp'].dt.tz_convert('America/New_York')
            df = df.set_index('timestamp')
            df = df.between_time('9:30', '15:45')
            #update data
            self.data[stock] = self.data[stock].append(df.tail(len(df.index)))
            self.data[stock] = self.data[stock].drop(index=self.data[stock].index[-1])
            for i in range(len(df.index)-1):
                self.data[stock] = self.data[stock].drop(index=self.data[stock].index[0])

    #calculate the 5ema of a stock
    def calculate(self):
        for stock in self.stocks:
            #once fully updated with the data - start replacing
            if self.count > 0:
                start = (self.api.get_clock().next_open - pd.tseries.offsets.BDay(1)).isoformat('T')
                df = self.api.get_bars(symbol=stock,    timeframe='15Min', start=start).df 
                df = df.reset_index()
                df['timestamp'] = df['timestamp'].dt.tz_convert('America/New_York')
                df = df.set_index('timestamp')
                df = df.between_time('9:30', '15:45')
                #update data
                self.data[stock] = self.data[stock].append(df.tail(1))
                self.data[stock] = self.data[stock].drop(index=self.data[stock].index[0])

            #calculate ema
            vals = self.data[stock].tail(10)['close']
            last_close = vals.iloc[-1]
            five_ema = vals.iloc[0]
            self.closes[stock] = last_close
            #calculate ema
            for val in vals:
                five_ema = (val*2)/6 + five_ema*(1-2/6)
            self.emas[stock] = five_ema

            self.count += 1

    def algorithm(self):
        self.collectData()
        while(self.api.get_clock().is_open == True):
            #clear out data
            self.emas = {}
            self.closes = {}
            self.positions = {}

            self.calculate()

            for stock in self.stocks:
                #get positions of each stock
                try:
                    qty = float(self.api.get_position(stock).qty)
                except Exception as exception:
                    if exception.__str__() == 'position does not exist':
                        qty = 0
                side = ''
                amount = 0
                if qty != 0:
                    side = self.api.get_position(stock).side
                    amount = self.api.get_position(stock).market_value
                self.positions[stock] = [qty, side]

                balance = float(self.api.get_account().equity)/2
                try:
                    power = balance/(len(self.stocks) - len(self.api.list_positions()))
                except ZeroDivisionError:
                    power = 0
                    qty = math.floor(power/self.closes.get(stock))

                now = datetime.datetime.now()
                
                #buy/sell based on 5ema
                if self.closes.get(stock) > self.emas.get(stock):
                    #if short then cover
                    if self.positions[stock][1] == 'short':
                        self.api.submit_order(symbol=stock, qty=qty, side='buy', type='market', time_in_force='day')
                        print('EXITED SHORT OF ', stock, 'FOR ', power, 'AT ', now)
                        
                    #if no poistion then go long
                    if self.positions[stock][0] == 0:
                        self.api.submit_order(symbol=stock, qty=qty, side='buy', type='market', time_in_force='day')
                        print('ENTERED LONG OF ', stock, 'FOR ', power, 'AT ', now)
                else:
                    #if long then sell
                    if self.positions[stock][1] == 'long':
                        self.api.submit_order(symbol=stock, qty=qty, side='sell', type='market', time_in_force='day')
                        print('EXITED LONG OF ', stock, 'FOR ', amount, 'AT ', now)
                    #if nothing open go short
                    if self.positions[stock][0] == 0:
                        self.api.submit_order(symbol=stock, qty=qty, side='sell', type='market', time_in_force='day')
                        print('ENTERED SHORT OF ', stock, 'FOR ', amount, 'AT ', now)
                
        print('balance is', float(self.api.get_account().equity))
        time.sleep(900)

#run the program
if __name__ == '__main__':
    Stock = fiveEMA()
    Stock.run() 