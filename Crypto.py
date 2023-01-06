import alpaca_trade_api as tradeapi
import time
from config import API_KEY, API_SECRET, API_URL

#TODO fix data collection
class fiveEMA:
    def __init__(self):
        #api data   
        self.api = tradeapi.REST(API_KEY, API_SECRET, API_URL, 'v2') 
        #cryptos to be traded
        self.cryptos = ['BTCUSD', 'ETHUSD', 'ATOMUSD', 'DOGEUSD', 'AAVEUSD', 'ALGOUSD', 'SOLUSD', 'DOTUSD', 'ADAUSD', 'MATICUSD']

        #maps to keep track of trades
        self.emas = {}
        self.closes = {}
        self.positions = {}
    
    #what will be run in main
    def run(self):
        #see if api connects properly
        print(self.api.get_account().status)
        self.algorithm()

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

    #calculate the 5ema of a crypto
    def calculate(self):
        for crypto in self.cryptos:
            data = self.api.get_crypto_bars(symbol=crypto,timeframe='15Min', exchanges='BNCU').df
            #reset timestamp index
            data = data.reset_index()
            #latest 5
            data = data.drop(data.index[-1])
            vals = data.tail(10)['close']
            #last close
            last_price = vals.iloc[-1]
            #calculate the previous 5ema
            five_ema = vals.iloc[0]
            #add close to the map
            self.closes[crypto] = last_price

            #set the 5ema of each crypto
            for val in vals['close']:
                five_ema = (val*2/6) + five_ema*(1-2/6)
            self.emas[crypto] = five_ema

    #get positions of each crypto
    def positioning(self):
        for crypto in self.cryptos:
            side = ''
            try:
                qty = float(self.api.get_position(crypto).qty)
                side = self.api.get_position(crypto).side
            except Exception as exception:
                if exception.__str__() == 'position does not exist':
                    qty = 0
            self.positions[crypto] = [qty, side]

    def algorithm(self):
        while(True):
            #clear out data
            self.emas = {}
            self.closes = {}
            self.positions = {}

            self.wait()
            self.calculate()
            self.positioning()

            #no short selling for cryptos, can only hold longs
            for crypto, ema in self.emas.items():
                #calculate balance and how much to purchase
                balance = float(self.api.get_account().equity)
                try:
                    power = balance/(len(self.cryptos) - len(self.api.list_positions()))
                except ZeroDivisionError:
                    power = 0

                #if the candle closes about the 5ema
                if self.closes[crypto] > ema:
                    #if there is no position currently, then buy
                    if self.positions[crypto][0] == 0:
                        self.api.submit_order(symbol=crypto, notional=power, side='buy', type='market', time_in_force='gtc')
                        print('Bought', power, 'worth of', crypto)

                #if the candle closes below the 5ema
                else:
                    #if the position is long, then sell
                    if self.positions[crypto][1] == 'long':
                        self.api.submit_order(symbol=crypto, qty=self.positions[crypto][0], side='sell', type='market', time_in_force='gtc')
                        print('Sold', self.positions[crypto][0], 'worth of', crypto)    

            #remaining balance on the account
            print('balance is', float(self.api.get_account().equity))

            #run every 15 mins (15min 5ema trade strategy)
            time.sleep(900)

#run the program
if __name__ == '__main__':
    Crypto = fiveEMA()
    Crypto.run() 