from stochastic.gbm_func import brownian_motion
from utils.load_stock import load_prices,load_ranks
import backtrader as bt
import sqlite3
import pandas as pd
import numpy as np
from utils.load_stock import load_prices
from utils.load_stock import load_ranks

#SQL Connect
conn = sqlite3.connect("../stock_prices.db")

#Prices
stock_prices = load_prices("CRSP", conn)

class GBMIndicator(bt.Indicator):
    lines = ('high_percentile', 'low_percentile', 'avg_price')
    params = (
        ('high_percentile', 80), #80
        ('low_percentile', 20), #20
        ('rolling_window_size', 30),
        ('simulation_paths', 500),
        ('prediction_horizon', 1/12)
    )

    def __init__(self):
        self.addminperiod(self.params.rolling_window_size)
        np.random.seed(42)
        self.dt = 1/252
        self.N = int(self.params.prediction_horizon/self.dt)

    def next(self):
        rolling_window_data = pd.Series(self.data.close.get(size=self.params.rolling_window_size))
        simulation = brownian_motion(rolling_window_data,
                        self.params.simulation_paths,
                        self.N,
                        self.dt,
                        self.params.rolling_window_size)
        final_prices = simulation[:, -1]
        percentiles = np.percentile(final_prices, [self.params.low_percentile, self.params.high_percentile])
        p_low = percentiles[0]
        p_high = percentiles[1]
        self.lines.high_percentile[0] = p_high
        self.lines.low_percentile[0] = p_low
        self.lines.avg_price[0] = final_prices.mean()


class GBMStrategy(bt.Strategy):

    def __init__(self):
        self.gbm = GBMIndicator()
        self.rsi = bt.talib.RSI(self.data, timeperiod=14)

    def next(self):
        if not self.position:
            if self.gbm.low_percentile[0] > self.data.close[0]:
                self.buy()
        elif self.position and self.data.close[0] < self.position.price * 0.95:  # 5% stop-loss
            self.sell()
        elif self.position and self.data.close[0] > self.position.price * 1.20:
            self.sell()
        else:
            if self.gbm.high_percentile[0] < self.data.close[0]:
                self.sell()


if __name__ == '__main__':
    cerebro = bt.Cerebro()
    #Data
    feed_prices = bt.feeds.PandasData(dataname=stock_prices)
    cerebro.adddata(feed_prices)

    #Strategy
    cerebro.addstrategy(GBMStrategy)

    #Cash
    cerebro.broker.setcash(10000)
    cerebro.broker.setcommission(0.001)
    cerebro.addsizer(bt.sizers.AllInSizerInt)

    #Analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')

    results = cerebro.run()
    cerebro.plot()

    print(f"Sharpe Ratio: {results[0].analyzers.sharpe.get_analysis()['sharperatio']}")
    print(f"Max Drawdown: {results[0].analyzers.drawdown.get_analysis()['max']['drawdown']}")
    print(f"Annual Return: {results[0].analyzers.returns.get_analysis()['rnorm']}")
