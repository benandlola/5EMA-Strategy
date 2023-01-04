# 5EMA Strategy
This algorithm is a cryptocurrency trader that uses the Alpaca API. It calculates the 15min 5ema for a list of cryptocurrencies and buys when the latest candle closes over the 5ema, or sells a long position if the candle closes below. Alpaca API doesn't allow for shorting cryptos so only a long strategy is used.

The algorithm will run at every 15 minute break point of an hour (00, 15, 30, or 45), plus add a minute for new data to come in and be the most up to date

Unfortunately due to Alpaca's free version, data is 15 minutes delayed so the ema and trades aren't actually executed in a timely manner. 