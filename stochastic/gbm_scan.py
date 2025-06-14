import math
import sqlite3

import numpy as np
import pandas as pd

from utils.get_all_available_tickers import get_all_available_tickers
from utils.load_stock import load_prices
from gbm_func import brownian_motion

available_stocks = pd.read_csv("../fundamentals/input/brokerage_available_stocks.csv")
print(available_stocks)

conn = sqlite3.connect('../stock_prices.db')

ticker_names = get_all_available_tickers(conn)
ticker_data = {}

for ticker_name in ticker_names:
    if available_stocks["act_symbol"].str.contains(ticker_name).any():
        print(f"{ticker_name}: Loading prices")
        prices = load_prices(ticker_name, conn)
        close_prices = prices['close']
        print(f"{ticker_name}: Simulating GBM")
        gbm = brownian_motion(
            simulation_paths=2000,
            prices = close_prices,
            n_days = 30,
            window_size=180
        )
        current_price = close_prices.iloc[-1]
        gbm_final_prices = gbm[:, -1]
        gbm_percentiles = np.percentile(gbm_final_prices, np.arange(101))
        ticker_data[ticker_name] = {
            'current_price': current_price,
            'gbm_percentiles': gbm_percentiles
        }
        print(f"{ticker_name}: Finished")
    else:
        print(f"{ticker_name} - skipping")

conn.close()

diff_list = []
for ticker_name, data in ticker_data.items():
    current_price = data['current_price']
    percentile_price = data['gbm_percentiles'][20]

    pct_diff = (percentile_price - current_price) / current_price * 100

    if not math.isfinite(pct_diff):
        continue

    diff_list.append({
        'ticker': ticker_name,
        'current_price': current_price,
        'percentile_price': percentile_price,
        'pct_diff': pct_diff
    })


sorted_diff_list = sorted(diff_list, key=lambda x: x['pct_diff'], reverse=False)

for item in sorted_diff_list:
    print(f"{item['ticker']}: {item['pct_diff']:.2f}% (Percentile price: {item['percentile_price']:.2f}, Current: {item['current_price']:.2f})")