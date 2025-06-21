def get_all_available_tickers(sql_conn):
    cursor = sql_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    return list(map(lambda x: x[0].removesuffix('_prices'), filter(lambda x: x[0].endswith('_prices'), tables)))