import math
import sqlite3
import pandas as pd
import numpy as np
from pylab import mpl, plt
import polars as pl

#Plotting settings
plt.style.use('seaborn-v0_8')
mpl.rcParams['font.family'] = 'serif'

#SQL connection
conn = sqlite3.connect("../stock_prices.db")

#Utils
default_rank_mapping = { 'HOLD': 0, 'Sell': -1, 'Strong Sell': -3, 'Buy': 1, 'Strong Buy': 3}

def prepare_data(ticker, conn, rank_mapping=default_rank_mapping):
    stock_ranks = pd.read_sql(f'SELECT date, rank FROM {ticker}_ranks', conn)
    stock_prices = pd.read_sql(f'SELECT * FROM {ticker}_prices', conn)

    stock_ranks['rank_num'] = stock_ranks['rank'].map(rank_mapping)
    stock_ranks_pl = pl.from_pandas(stock_ranks)
    stock_prices_pl = pl.from_pandas(stock_prices)

    stock_ranks_rolling = stock_ranks_pl \
        .with_columns([
        pl.col("date").cast(pl.Date),
    ]) \
        .rolling(index_column='date', period='9mo', closed='both') \
        .agg([
        pl.col("rank_num").sum().alias("rank_sum"),
        pl.col("rank_num").mean().alias("rank_mean"),
        pl.col("rank_num").std().alias("rank_std"),
        pl.col("rank_num").count().alias("rank_count"),
    ])

    stock_result_pl = stock_prices_pl.with_columns([
        pl.col("date").cast(pl.Date)
    ]).join_asof(
        stock_ranks_rolling,
        left_on='date',
        right_on='date',
        strategy='backward'
    )
    return stock_result_pl.to_pandas()

def apply_strategy(stock_data):
    stock_data['log_return'] = np.log(stock_data['close'] / stock_data['close'].shift(1))
    stock_data['positions'] = np.where(stock_data['rank_mean'] > 0, 1, 0)
    stock_data['strategy_log_return'] = stock_data['log_return'] * stock_data['positions']
    stock_data['strategy_result'] = np.exp(stock_data['strategy_log_return'].cumsum())

def efficient_frontier(u, cov_matrix):
    weights = np.ones(u.shape)
    weights_candidates = np.random.dirichlet(weights, size=100)
    Rp = weights_candidates @ u
    Stdp = np.sqrt(np.sum(weights_candidates @ cov_matrix * weights_candidates, axis=1)).to_numpy()
    Sharpe = Rp / Stdp
    frontier_np = np.hstack((weights_candidates, Rp.reshape(-1,1), Stdp.reshape(-1,1), Sharpe.reshape(-1,1)))

    frontier_df = pd.DataFrame(frontier_np)
    column_names = {frontier_df.columns[-3]: 'Rp', frontier_df.columns[-2]: 'Stdp', frontier_df.columns[-1]: 'Sharpe'}
    frontier_df.rename(columns=column_names, inplace=True)
    return frontier_df

crsp = prepare_data('CRSP', conn)
crsp = crsp.set_index('date')
apply_strategy(crsp)
crsp_c = crsp.add_prefix('CRSP_')

sbsw = prepare_data('SBSW', conn)
sbsw = sbsw.set_index('date')
apply_strategy(sbsw)
sbsw_c = sbsw.add_prefix('SBSW_')

ntla = prepare_data('NTLA', conn)
ntla = ntla.set_index('date')
apply_strategy(ntla)
ntla_c = ntla.add_prefix('NTLA_')

stock_data = pd.concat([crsp_c, ntla_c, sbsw_c], axis=1).dropna()
cov_matrix = stock_data[['CRSP_rank_sum', 'SBSW_rank_sum', 'NTLA_rank_sum']].cov()

#Efficient frontier
frontier = efficient_frontier(
    stock_data[['CRSP_rank_mean', 'SBSW_rank_mean', 'NTLA_rank_mean']].iloc[-1].to_numpy(),
    cov_matrix)

def best_weights(row):
    expected_return = row[['CRSP_rank_mean', 'SBSW_rank_mean', 'NTLA_rank_mean']].to_numpy()
    frontier = efficient_frontier(
        expected_return,
        cov_matrix)
    return pd.Series(frontier.loc[frontier['Sharpe'].idxmax(), [0,1,2]])


stock_data[['w1', 'w2', 'w3']] = stock_data.apply(best_weights, axis=1)
stock_data['strategy_log_return_frontier'] = np.sum(stock_data[['w1', 'w2', 'w3']].to_numpy() * stock_data[['CRSP_strategy_log_return', 'SBSW_strategy_log_return', 'NTLA_strategy_log_return']], axis=1)
stock_data['strategy_log_return_random'] = np.sum(np.array((0.333, 0.333, 0.333)) * stock_data[['CRSP_strategy_log_return', 'SBSW_strategy_log_return', 'NTLA_strategy_log_return']], axis=1)
stock_data['strategy_frontier_result'] = np.exp(stock_data['strategy_log_return_frontier'].cumsum())
stock_data['strategy_result'] = np.exp(stock_data['strategy_log_return_random'].cumsum())


#Plotting
plt.figure(figsize=(12,8))
ax1 = plt.subplot(511)
ax1.set_title("CRSP")
crsp[['close', 'rank_mean']].plot(ax=ax1, secondary_y=['rank_mean'])

ax2 = plt.subplot(512)
ax2.set_title("SBSW")
sbsw[['close', 'rank_mean']].plot(ax=ax2, secondary_y=['rank_mean'])

ax3 = plt.subplot(513)
ax3.set_title("NTLA")
ntla[['close', 'rank_mean']].plot(ax=ax3, secondary_y=['rank_mean'])

ax4 = plt.subplot(514)
stock_data[['w1', 'w2', 'w3']].plot(ax=ax4)
ax4.legend(["CRSP weight", "SBSW weight", "NTLA weight"])

ax5 = plt.subplot(515)
stock_data[['strategy_frontier_result', 'strategy_result']].plot(ax=ax5)
ax5.legend(["ROI - efficient frontier weights", "ROI - all weights equal"])

plt.show()

