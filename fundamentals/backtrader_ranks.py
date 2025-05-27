import backtrader as bt
import sqlite3
import pandas as pd
from utils.load_stock import load_prices
from utils.load_stock import load_ranks

#SQL connection
conn = sqlite3.connect("../stock_prices.db")
#Get data
stock_prices = load_prices("CRSP", conn)

class RankSMA(bt.Indicator):
    lines = ('rank_sma',)
    params = (
        ('window_size_months', 3),
        ('hold_value', 0.0),
        ('sell_value', -1.0),
        ('strong_sell', -3.0),
        ('strong_buy', 3.0),
        ('buy', 1.0)
    )

    def __init__(self):
        default_rank_mapping = {'Hold': self.params.hold_value, 'Sell': self.params.sell_value, 'Strong Sell': self.params.strong_sell, 'Buy': self.params.buy, 'Strong Buy': self.params.strong_buy}
        self.stock_ranks = load_ranks("CRSP", conn)
        self.stock_ranks['rank_num'] = self.stock_ranks['rank'].map(default_rank_mapping)
        pass

    def next(self):
        tick_date = pd.to_datetime(self.data.datetime.date(0))
        start_date = tick_date - pd.DateOffset(months=self.params.window_size_months)
        ranks = self.stock_ranks[(self.stock_ranks.index < tick_date)
                                 & (self.stock_ranks.index > start_date)]
        rank_avg = ranks['rank_num'].mean()
        self.lines.rank_sma[0] = rank_avg


class RankStrategy(bt.Strategy):
    params = (
        ('buy_signal_threshold', 0),
        ('sell_signal_threshold', 0)
    )

    def __init__(self):
        self.ranks = RankSMA()

    def next(self):
        if not self.position:
            if self.ranks[0] > self.params.buy_signal_threshold:
                self.buy()
        else:
            if self.ranks[0] < self.params.sell_signal_threshold:
                self.sell()

feed_prices = bt.feeds.PandasData(dataname=stock_prices)
cerebro = bt.Cerebro()
cerebro.adddata(feed_prices)
cerebro.addstrategy(RankStrategy)
cerebro.broker.setcash(10000)
cerebro.broker.setcommission(0.001)
cerebro.addsizer(bt.sizers.AllInSizerInt)


cerebro.run()
cerebro.plot()




