import backtrader as bt
import sqlite3
import pandas as pd
from scipy.optimize import brute
from scipy.optimize import fmin
from utils.load_stock import load_prices

#SQL connection
conn = sqlite3.connect("../stock_prices.db")
#Get data
stock_prices = load_prices("CRSP", conn)

class BBandsStrategy(bt.Strategy):
    params = (
        ('period', 44),
        ('nbdevup', 3.1),
        ('nbdevdn', 3.1),
        ('matype', 0)
    )

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.bbands = bt.talib.BBANDS(self.data.close,
                                      timeperiod=self.params.period,
                                      nbdevup=self.params.nbdevup,
                                      nbdevdn=self.params.nbdevdn,
                                      matype=self.params.matype)
        self.order = None

    def next(self):
        if not self.position:
            if self.bbands.lowerband[0] >= self.dataclose:
                self.order = self.buy()
        else:
            if self.bbands.upperband[0] <= self.dataclose:
                self.order = self.sell()


    def stop(self):
        print(f"Profit for: ({self.params.period}, {self.params.nbdevup}, {self.params.nbdevdn}) "
              f"-> {self.broker.getvalue()}")

feed_prices = bt.feeds.PandasData(dataname=stock_prices)

def bbands_strategy(params):
    period, nbdevup, nbdevdn = params
    period = int(period)
    cerebro = bt.Cerebro()

    cerebro.adddata(feed_prices)
    cerebro.addstrategy(BBandsStrategy, period=period, nbdevup=nbdevup, nbdevdn=nbdevdn)
    cerebro.broker.setcash(10000)
    cerebro.broker.setcommission(0.001)
    #cerebro.addsizer(bt.sizers.FixedSize, stake=100)
    cerebro.addsizer(bt.sizers.AllInSizerInt)

    return cerebro


def backtest_to_optimise(params):
    results = bbands_strategy(params).run()
    return -results[0].broker.getvalue()

ranges = (
    slice(10, 40, 1),
    (1,3,0.1),
    (1,3,0.1)
)

if __name__ == '__main__':
    result = brute(func=backtest_to_optimise,
                   ranges=ranges,
                   full_output=False,
                   finish=fmin,
                   workers=8)

    print(result)

    best_fit = bbands_strategy(result)
    best_fit.run()
    best_fit.plot()
