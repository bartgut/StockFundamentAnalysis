import backtrader as bt
import sqlite3
import pandas as pd

#Cerebro broker
cerebro = bt.Cerebro()
cerebro.broker.setcash(10000)
cerebro.broker.setcommission(0.001)

#SQL connection
conn = sqlite3.connect("../stock_prices.db")

#Get data
stock_prices = pd.read_sql(f'SELECT * FROM CRSP_prices', conn)
stock_prices['date'] = pd.to_datetime(stock_prices['date'])
stock_prices.set_index('date', inplace=True)

class TestStrategy(bt.Strategy):
    params = (
        ('rsi_low', 30),
        ('rsi_high',70)
    )

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.dataclose = self.datas[0].close

        bt.indicators.ExponentialMovingAverage(self.datas[0], period=25)
        self.rsi = bt.indicators.RSI(self.datas[0])
        self.order = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, %.2f' % order.executed.price)
            elif order.issell():
                self.log('SELL EXECUTED, %.2f' % order.executed.price)

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        if self.order:
            return

        if not self.position:
            if self.rsi[0] < self.params.rsi_low:
                self.order = self.buy()
        else:
            if self.rsi[0] >= self.params.rsi_high:
                self.order = self.sell()




feed_prices = bt.feeds.PandasData(dataname=stock_prices)
cerebro.adddata(feed_prices)
#strats = cerebro.optstrategy(TestStrategy,rsi_low=range(10,11), rsi_high=range(60,65))
cerebro.addstrategy(TestStrategy, rsi_low=30, rsi_high=70)
cerebro.addsizer(bt.sizers.FixedSize, stake=1)


print(f"Starting with: {cerebro.broker.getvalue()}")

cerebro.run(maxcpus=1)
cerebro.plot()

print(f"Final value: {cerebro.broker.getvalue()}")