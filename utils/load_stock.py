import sqlite3
import pandas as pd

def load_prices(ticker, sql_conn):
    stock_prices = pd.read_sql(f'SELECT * FROM {ticker}_prices', sql_conn)
    stock_prices['date'] = pd.to_datetime(stock_prices['date'])
    stock_prices.set_index('date', inplace=True)
    return stock_prices
