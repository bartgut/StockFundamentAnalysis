import sqlite3
import pandas as pd

def load_prices(ticker, sql_conn):
    stock_prices = pd.read_sql(f'SELECT * FROM {ticker}_prices', sql_conn)
    stock_prices['date'] = pd.to_datetime(stock_prices['date'])
    stock_prices.set_index('date', inplace=True)
    return stock_prices

def load_ranks(ticker, sql_conn):
    stock_ranks = pd.read_sql(f'SELECT * FROM {ticker}_ranks', sql_conn)
    stock_ranks['date'] = pd.to_datetime(stock_ranks['date'])
    stock_ranks.set_index('date', inplace=True)
    return stock_ranks

