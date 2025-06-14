from stochastic.gbm_func import brownian_motion
from utils.get_all_available_tickers import get_all_available_tickers
from utils.load_stock import load_prices,load_ranks
import backtrader as bt
import sqlite3
import pandas as pd
import numpy as np
from utils.load_stock import load_prices
from utils.load_stock import load_ranks
import statsmodels.api as sm
import scipy.stats as scs
from pylab import plt

#SQL Connect
conn = sqlite3.connect("../stock_prices.db")

#Prices
stock_prices = load_prices("ZVV", conn)
log_returns = np.log(stock_prices['close'] / stock_prices['close'].shift(1)).dropna()

print(f"Normal test: {scs.normaltest(log_returns)[1]}")
sm.qqplot(log_returns, line='s')
plt.show()

available_stocks = pd.read_csv("../fundamentals/input/brokerage_available_stocks.csv")

conn = sqlite3.connect('../stock_prices.db')

all_tickers = get_all_available_tickers(conn)

ticker_data = []

for ticker_name in all_tickers:
    prices = load_prices(ticker_name, conn)
    log_returns = np.log(prices['close'] / prices['close'].shift(1)).dropna()
    norm_test = scs.normaltest(log_returns)[1]
    ticker_data.append({
        'ticker_name': ticker_name,
        'norm_test_res': norm_test
    })

sorted_diff_list = sorted(ticker_data, key=lambda x: x['norm_test_res'], reverse=False)

for item in sorted_diff_list:
    print(f"{item['ticker_name']}: {item['norm_test_res']:.5f}%")