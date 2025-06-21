import time

import dash
from dash import Dash, html, dcc, callback, Output, Input, State, dash_table, DiskcacheManager
import plotly.express as px
import pandas as pd
import sqlite3
import numpy as np

from stochastic.gbm_func import brownian_motion
from utils.get_all_available_tickers import get_all_available_tickers
from utils.load_stock import load_prices
import diskcache

cache = diskcache.Cache("./cache")
background_callback_manager = DiskcacheManager(cache)

conn = sqlite3.connect('../stock_prices.db', check_same_thread=False)

ticker_names = get_all_available_tickers(conn)
xtb_available_tickers = pd.read_csv("../fundamentals/input/brokerage_available_stocks.csv")

var_confidence_level = 0.95

window_size = range(60, 180, 10)
prediction_horizon = range(30, 360, 30)

app = Dash()

app.layout = [
    html.H1(children='Stock dashboard', style={'textAlign': 'center'}),
    dcc.Dropdown(pd.Series(ticker_names), 'CRSP', id='dropdown-selection'),
    dcc.RadioItems(id='broker',
                  options=[
                      {'label': 'Show all ', 'value': 'all'},
                      {'label': 'XTB', 'value': 'xtb'}
                  ],
                  value='all'),
    html.Div(children=[
        html.Div(children=[
            html.H2(children="Stock returns"),
            dcc.Graph(id='stock-main-chart'),
        ], style={'flex': 1}),
        html.Div(children=[
            html.H2(children="Log returns"),
            dcc.Graph(id='stock-log-returns')
        ], style={'flex': 1})
    ], style={'display': 'flex', 'flexDirection': 'row'}),
    html.Div(children=[
        html.Div(children=[
            html.H2(children="Geometric Brownian motion simulation"),
            dcc.Graph(id='gbm_var'),
        ], style={'flex': 1}),
        html.Div(children=[
            html.H2(children="Settings"),
            html.H4(children="Rolling window"),
            dcc.Slider(
                window_size.start,
                window_size.stop,
                window_size.step,
                value=window_size.start,
                id='window-size-slider'
            ),
            html.H4(children="Prediction horizon(days)"),
            dcc.Slider(
                prediction_horizon.start,
                prediction_horizon.stop,
                prediction_horizon.step,
                value=prediction_horizon.start,
                id='prediction-horizon-slider'
            )

        ], style={'flex': 1}),
    ], style={'display': 'flex', 'flexDirection': 'row'}),
    dash_table.DataTable(id='table', page_size=10),
    html.H2(children="GBM simulation"),
    html.Div(id="current-window-size"),
    html.Div(id="current-prediction-horizon"),
    html.Button(id="gbm-scan-button", children="Run GBM simulation over all stocks"),
    dash_table.DataTable(id="gbm-scan-table", page_size=20, sort_action='native')
]

@callback(
    Output('current-window-size', 'children'),
    Input('window-size-slider', 'value')
)
def update_current_window_size(window_size):
    return f"Selected window size: {window_size}"

@callback(
    Output('current-prediction-horizon', 'children'),
    Input('prediction-horizon-slider', 'value')
)
def update_current_prediction_horizon(prediction_horizon):
    return f"Selected prediction horizon: {prediction_horizon}"

@callback(
    Output('dropdown-selection', 'options'),
    Input('broker', 'value')
)
def update_dropdown(selected_brokerage):
    return get_available_tickers(selected_brokerage)

@callback(
    Output('stock-main-chart', 'figure'),
    Input('dropdown-selection', 'value')
)
def update_stock_main_chart(value):
    dff = load_prices(value, conn).reset_index()
    fig = px.line(dff, x='date', y='close')
    fig.update_layout(transition_duration=500)
    return fig

@callback(
    Output('stock-log-returns', 'figure'),
    Input('dropdown-selection', 'value')
)
def update_stock_log_returns(value):
    dff = load_prices(value, conn)
    dff['log_returns'] = np.log(dff['close'] / dff['close'].shift(1)).dropna()
    fig = px.histogram(dff, x='log_returns', nbins=100)
    fig.update_layout(transition_duration=500)
    return fig

@callback(
    Output('gbm_var', 'figure'),
    Input('dropdown-selection', 'value'),
    Input('window-size-slider', 'value'),
    Input('prediction-horizon-slider', 'value')
)
def update_gbm_var(ticker_name, window_size, prediction_horizon):
    dff = load_prices(ticker_name, conn)
    gbm_simulation = brownian_motion(dff['close'],
                                     simulation_paths=2000,
                                     window_size=window_size,
                                     n_days=prediction_horizon)
    gbm_final_prices = gbm_simulation[:, -1]

    initial_price = dff['close'].iloc[-1]
    var = np.percentile(gbm_final_prices - initial_price, 100 * (1 - var_confidence_level))
    fig = px.histogram(gbm_final_prices)

    fig.add_vline(
        x=initial_price + var,
        line_dash="dash",
        line_color="red",
        annotation_text=f"VaR (95%): {var:.2f}",
        annotation_position="top left"
    )

    fig.add_vline(
        x=initial_price,
        line_dash="solid",
        line_color="green",
        annotation_text=f"Initial Price: {initial_price:.2f}",
        annotation_position="top right"
    )

    fig.update_layout(transition_duration=2000)
    return fig

@callback(
    Output('table', 'data'),
    Input('dropdown-selection', 'value')
)
def update_table(value):
    dff = load_prices(value, conn).reset_index()
    return dff.to_dict('records')

@callback(
    Output('gbm-scan-table', 'data'),
    Input('gbm-scan-button', 'n_clicks'),
    State('window-size-slider', 'value'),
    State('prediction-horizon-slider', 'value'),
    State('broker', 'value'),
    background=True,
    manager=background_callback_manager,
    running=[
        (Output("gbm-scan-button", "disabled"), True, False),
    ]
)
def update_clicks(n_clicks, window_size, prediction_horizon, selected_brokerage):
    if not n_clicks:
        return dash.no_update
    tickers_to_scan = get_available_tickers(selected_brokerage)

    simulation_results = []

    for ticker_name in tickers_to_scan:
        prices = load_prices(ticker_name, conn)
        close_prices = prices['close']
        gbm = brownian_motion(
            simulation_paths=2000,
            prices = close_prices,
            n_days = prediction_horizon,
            window_size=window_size
        )
        gbm_final_prices = gbm[:, -1]
        current_close_price = close_prices.iloc[-1]
        gbm_mean = np.mean(gbm_final_prices)
        var = np.percentile(gbm_final_prices - current_close_price, 100 * (1 - var_confidence_level))
        var_percent = (var / current_close_price) * 100

        simulation_results.append({
            'Ticker': ticker_name,
            'Current close price': round(current_close_price, 2),
            'Avg simulated price': round(gbm_mean, 2),
            'VaR 5% (abs)': var,
            'VaR (%)': var_percent
        })

    return simulation_results


def get_available_tickers(selected_brokerage):
    if selected_brokerage == 'all':
        return ticker_names
    if selected_brokerage == 'xtb':
        return list(filter(lambda ticker_name: ticker_name in xtb_available_tickers['act_symbol'].values, ticker_names))
    else:
        return ticker_names



if __name__ == '__main__':
    app.run(debug=True)