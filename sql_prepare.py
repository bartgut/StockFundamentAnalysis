import pandas as pd
import sqlite3

#Reading input data
df_prices = pd.read_csv("fundamentals/input/prices.csv")
df_ranks = pd.read_csv("fundamentals/input/ranks.csv")

conn = sqlite3.connect("stock_prices.db")

for name, stock_data in df_prices.groupby('act_symbol'):
    standarized_name = name.replace(',', '_')
    stock_data.to_sql(f"{name}_prices", conn, if_exists='replace', index=False)

for name, stock_ranks in df_ranks.groupby('act_symbol'):
    standarized_name = name.replace(',', '_')
    stock_ranks.to_sql(f"{name}_ranks", conn, if_exists='replace', index=False)




