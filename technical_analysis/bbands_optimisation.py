import math
import sqlite3

import numpy as np
import pandas as pd
from pylab import mpl, plt
import talib
import scipy.optimize as sco
import backtrader as bt

print(talib.get_functions())
#Plotting settings
plt.style.use('seaborn-v0_8')
mpl.rcParams['font.family'] = 'serif'

#SQL connection
conn = sqlite3.connect("../stock_prices.db")

#Get data
stock_prices = pd.read_sql(f'SELECT * FROM CRSP_prices', conn)

def keltner(params, df):
    period, nbdevup, nbdevdn = params
    period = int(period)
    bb = talib.BBANDS(df['close'], timeperiod=period, nbdevup=nbdevup, nbdevdn=nbdevdn, matype=0)
    new_df = df.copy()
    new_df['upper_band'] = bb[0]
    new_df['average'] = bb[1]
    new_df['lower_band'] = bb[2]
    new_df['signal'] = 0
    new_df.loc[new_df['close'] < new_df['lower_band'], 'signal'] = 1
    new_df.loc[new_df['close'] > new_df['upper_band'], 'signal'] = -1
    new_df['position'] = new_df['signal'].replace(0, np.nan).ffill().fillna(0)
    new_df['log_returns'] = np.log(new_df['close'] / new_df['close'].shift(1))
    new_df['strategy_log_return'] = new_df['log_returns'] * new_df['position']
    new_df['strategy_return'] = np.exp(new_df['strategy_log_return'].cumsum())
    return new_df

def res(df):
    return -df['strategy_return'].iloc[-1]

def to_optimize(params):
    res_df = keltner(params, stock_prices)
    return res(res_df)

best = sco.brute(to_optimize, (slice(2, 50, 1), slice(0.1,10,0.5), slice(0.1,10,0.5)), finish=None, disp=True)

print(best)

print(to_optimize(best))


best_df = keltner((44,3.1,3.1), stock_prices)

plt.figure(figsize=(12,8))
ax1 = plt.subplot(211)
best_df[['close', 'upper_band', 'average', 'lower_band']].plot(ax=ax1)
ax2 = plt.subplot(212)
best_df['strategy_return'].plot(ax=ax2)



plt.show()

#res_df = keltner(stock_prices, 20, 2,2)
#strategy_res = res(res_df)

#print(strategy_res)

#print(res_df.describe())


