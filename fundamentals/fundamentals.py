import polars as pl
import plotly.graph_objects as go
import os

# Read files
prices_df = pl.read_csv("input/prices.csv")
income_df = pl.read_csv("input/income_statements.csv")
brokerage_df = pl.read_csv("input/brokerage_available_stocks.csv")

#Filter needed data
available_symbols = brokerage_df["act_symbol"]
prices_df = prices_df.filter(pl.col("act_symbol").is_in(available_symbols))
income_df = income_df\
    .filter(pl.col("act_symbol").is_in(available_symbols))\
    .filter(pl.col("period") == "Quarter")


#Map dates
prices_df = prices_df.with_columns(
    pl.col("date").str.strptime(pl.Date, "%Y-%m-%d")
)
income_df = income_df.with_columns(
    pl.col("date").str.strptime(pl.Date, "%Y-%m-%d")
)

#join prices with income statements
result_df = prices_df.join_asof(
    income_df.select(["act_symbol", "date", "average_shares", "sales", "period"]),
    left_on="date",
    right_on="date",
    by="act_symbol",
    strategy="backward"
).with_columns([
    (pl.col("close") * pl.col("average_shares")).alias("market_cap"),
])


#add medians:
result_df = result_df.group_by("act_symbol")\
    .map_groups(
        lambda group: group.sort('date')
            .with_columns([
            pl.col("market_cap").rolling_median(window_size=252 * 3, min_samples=1).alias("market_cap_3y_median"),
            pl.col("market_cap").rolling_median(window_size=252 * 5, min_samples=1).alias("market_cap_5y_median")
            ])
)

def create_symbol_plots(symbol_df, symbol):
    dates = symbol_df["date"].to_list()
    market_cap = symbol_df["market_cap"].to_list()
    market_cap_3y_median = symbol_df["market_cap_3y_median"].to_list()
    market_cap_5y_median = symbol_df["market_cap_5y_median"].to_list()

    fig_mc = go.Figure()
    fig_mc.add_trace(go.Scatter(
        x=dates,
        y=market_cap,
        name="Market Cap",
        line=dict(color="#4cc9f0", width=2),
        mode="lines+markers",
        marker=dict(size=4)
    ))
    fig_mc.add_trace(go.Scatter(
        x=dates,
        y=market_cap_3y_median,
        name="3Y Median",
        line=dict(color="#f48c06", width=2, dash="dash"),
        opacity=0.7
    ))
    fig_mc.add_trace(go.Scatter(
        x=dates,
        y=market_cap_5y_median,
        name="5Y Median",
        line=dict(color="#2fb32f", width=2, dash="dot"),
        opacity=0.7
    ))
    fig_mc.update_layout(
        title=dict(
            text=f"{symbol} Market Capitalization",
            font=dict(size=20, color="#ffffff"),
            x=0.5,
            xanchor="center"
        ),
        xaxis_title="Date",
        yaxis_title="Market Cap ($)",
        template="plotly_dark",
        hovermode="x unified",
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(0,0,0,0.5)",
            font=dict(color="#ffffff")
        ),
        plot_bgcolor="#1e2226",
        paper_bgcolor="#1e2226",
        font=dict(color="#ffffff"),
        xaxis=dict(
            gridcolor="rgba(255,255,255,0.1)",
            zerolinecolor="rgba(255,255,255,0.1)"
        ),
        yaxis=dict(
            gridcolor="rgba(255,255,255,0.1)",
            zerolinecolor="rgba(255,255,255,0.1)"
        )
    )
    fig_mc.update_traces(hovertemplate="%{x|%Y-%m-%d}<br>%{y:,.2f}")

    os.makedirs("charts", exist_ok=True)
    fig_mc.write_html(f"charts/{symbol}_market_cap.html")

for symbol in result_df["act_symbol"].unique():
    symbol_data = result_df.filter(pl.col("act_symbol") == symbol)
    create_symbol_plots(symbol_data, symbol)

summary_df = (
    result_df.group_by("act_symbol")
    .agg([
        pl.col("market_cap").sort_by("date").last().alias("latest_market_cap"),
        pl.col("market_cap_3y_median").sort_by("date").last().alias("latest_market_cap_3y_median"),
    ])
    .with_columns(
        ((pl.col("latest_market_cap") - pl.col("latest_market_cap_3y_median")) / pl.col("latest_market_cap_3y_median") * 100).alias(
            "market_cap_median_percentage_diff")
    )
    .sort(["market_cap_median_percentage_diff"])
)

html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Stock Summary</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f8f9fa; }
        table { border-collapse: collapse; width: 100%; max-width: 800px; margin: 20px auto; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: right; }
        th { background-color: #1f77b4; color: white; }
        tr:nth-child(even) { background-color: #f2f2f2; }
        tr:hover { background-color: #ddd; }
        a { color: #1f77b4; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <h1>Stock Summary Sorted by Market Cap</h1>
    <table>
        <tr>
            <th>Symbol</th>
            <th>Market Cap ($)</th>
            <th>3Y median diff</th>
        </tr>
"""

for row in summary_df.rows(named=True):
    symbol = row["act_symbol"]
    market_cap = f"{row['latest_market_cap']:,.2f}" if row["latest_market_cap"] is not None else "N/A"
    market_cap_diff = f"{row['market_cap_median_percentage_diff']:,.2f}" if row["market_cap_median_percentage_diff"] is not None else "N/A"
    html_content += f"""
        <tr>
            <td>
                <a href="{symbol}_market_cap.html">{symbol}</a> |
            </td>
            <td>{market_cap}</td>
            <td>{market_cap_diff}</td>
        </tr>
    """

html_content += """
    </table>
</body>
</html>
"""

# Write index.html
os.makedirs("charts", exist_ok=True)
with open("charts/index.html", "w") as f:
    f.write(html_content)

print("Charts and index.html have been generated and saved in the 'charts' directory.")