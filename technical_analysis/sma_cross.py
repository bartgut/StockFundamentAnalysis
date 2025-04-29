import numpy as np
import pandas as pd
from pylab import mpl, plt

#Reading input data
df = pd.read_csv("../fundamentals/input/prices.csv")

#Pivoting and getting data
df = df.pivot(index='date', columns='act_symbol', values='close')
crsp_stock = df[['CRSP']].copy().dropna().rename(columns={'CRSP': 'price'})
crsp_stock['SMA1'] = crsp_stock['price'].rolling(window=42).mean()
crsp_stock['SMA2'] = crsp_stock['price'].rolling(window=252).mean()
crsp_stock['positions'] = np.where(crsp_stock['SMA1'] > crsp_stock['SMA2'],1,0)

crsp_stock['log_returns'] = np.log(crsp_stock['price'] / crsp_stock['price'].shift(1))
crsp_stock['strategy_log_return'] = (crsp_stock['log_returns'] * crsp_stock['positions'])
crsp_stock['strategy_return'] = np.exp(crsp_stock['strategy_log_return'].cumsum())

print(crsp_stock.describe())

#Plotting
plt.figure(figsize=(11,7))
ax1 = plt.subplot(211)
crsp_stock[['price', 'SMA1', 'SMA2', 'positions']].plot(ax=ax1, secondary_y='positions')

#Strategy return
ax2 = plt.subplot(212)
crsp_stock[['strategy_return']].plot(ax=ax2)
plt.show()




