# importing required libraries
import pandas as pd
import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
from alpha_vantage.timeseries import TimeSeries
import ta

# read the currency codes
code_from = pd.read_excel("curcode.xlsx", sheet_name=0)
curcode_from = code_from["From"].tolist()
code_to = pd.read_excel("curcode.xlsx", sheet_name=1)
curcode_to = code_to["To"].tolist()

# initiate the app
app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    external_stylesheets=[dbc.themes.MINTY],
)
server = app.server

# app layout
app.layout = html.Div(
    children=[
        html.H1("Forex Tracker", style={"textAlign": "center"}),
        # the from currency dropdown
        html.Div(
            [
                html.H3("From Currency", style={"paddingRight": "30px"}),
                dcc.Dropdown(
                    id="FromCurrency",
                    options=[{"label": i, "value": i} for i in curcode_from],
                    value=curcode_from[curcode_from.index("EUR")],
                    clearable=False,
                    style={"fontsize": 15, "width": 75},
                ),
            ],
            style={
                "display": "inline-block",
                "verticalAlign": "middle",
                "paddingBottom": "5px",
                "paddingLeft": "10px",
            },
        ),
        # to currency dropdown
        html.Div(
            [
                html.H3("To Currency"),
                dcc.Dropdown(
                    id="ToCurrency",
                    options=[{"label": i, "value": i} for i in curcode_to],
                    value=curcode_to[curcode_to.index("USD")],
                    clearable=False,
                    style={"fontsize": 15, "width": 75},
                ),
            ],
            style={
                "display": "inline-block",
                "verticalAlign": "middle",
                "paddingBottom": "5px",
            },
        ),
        # the submit button
        html.Div(
            [
                html.Button(
                    id="submit-button",
                    n_clicks=0,
                    children="View",
                    style={"fontSize": 18, "marginLeft": "20px"},
                )
            ],
            style={
                "display": "inline-block",
                "verticalAlign": "bottom",
                "paddingBottom": "5px",
            },
        ),
        # the graphs
        dcc.Graph(id="candle"),
        dcc.Graph(id="bollinger"),
        dcc.Graph(id="macd"),
        dcc.Graph(id="rsi"),
        # the refresher
        dcc.Interval(
            id="interval-component",
            interval=60 * 1000,  # in milliseconds
            n_intervals=0,
        ),
    ]
)

# app functions
@app.callback(
    [
        Output(component_id="candle", component_property="figure"),
        Output(component_id="bollinger", component_property="figure"),
        Output(component_id="macd", component_property="figure"),
        Output(component_id="rsi", component_property="figure"),
    ],
    [Input("interval-component", "n_intervals"), Input("submit-button", "n_clicks")],
    [
        State(component_id="FromCurrency", component_property="value"),
        State(component_id="ToCurrency", component_property="value"),
    ],
)

# start the function
def RealTimeCurrencyExchangeRate(n_clicks, n_intervals, from_currency, to_currency):

    # initialize the api
    ts = TimeSeries(key="HUJ3ZZZOFB3IY9NE", output_format="pandas")

    # get the data
    time_data, metadata = ts.get_intraday(
        symbol=from_currency + to_currency, interval="1min", outputsize="full"
    )

    # sort the data frame in ascending order as per date and time
    time_data = time_data.sort_index()

    # keep the last 500 data points to calculate the indicators
    # time_data = time_data.iloc[-500:, ]

    # prepare data for 5 min candlestick chart
    # slice the last 104 rows
    time_c = time_data.iloc[
        -104:,
    ]
    # get the 5 minute highs and lows
    time_c["5m high"] = time_c["2. high"].rolling(5).max()
    time_c["5m low"] = time_c["3. low"].rolling(5).min()
    # filter out the na rows
    time_ct = time_c[pd.notnull(time_c["5m high"])]
    # reverse the order to get each 5 rows from last
    time_ct = time_ct.iloc[
        ::-1,
    ]
    # get each 5 rows from last
    time_ct = time_ct.iloc[
        ::5,
    ]
    # now reverse the order again
    time_ct = time_ct.iloc[
        ::-1,
    ]

    # Initialize Bollinger Bands Indicator
    indicator_bb = ta.volatility.BollingerBands(
        close=time_data["4. close"], window=60, window_dev=2
    )

    # Add Bollinger Bands features
    time_data["bb_bbm"] = indicator_bb.bollinger_mavg()
    time_data["bb_bbh"] = indicator_bb.bollinger_hband()
    time_data["bb_bbl"] = indicator_bb.bollinger_lband()

    # initiate macd
    trend_macd = ta.trend.MACD(
        close=time_data["4. close"], window_slow=26, window_fast=12, window_sign=9
    )

    # add macd features
    time_data["macd"] = trend_macd.macd()
    time_data["macd_signal"] = trend_macd.macd_signal()
    # time_data['macd_hist'] = time_data["macd"]-time_data["macd_signal"]
    time_data["macd_hist"] = trend_macd.macd_diff()

    # initiate rsi
    momentum_rsi = ta.momentum.RSIIndicator(close=time_data["4. close"], window=60)

    # add rsi feature
    time_data["rsi"] = momentum_rsi.rsi()

    # keep only the last 100 data points for charting
    time_dt = time_data.iloc[
        -100:,
    ]

    # make candlestick chart
    can_tim = go.Scatter(
        x=time_ct.index, y=time_ct["4. close"], line=dict(color="#034f84", dash="dot")
    )
    candleplot = go.Candlestick(
        x=time_ct.index,
        open=time_ct["1. open"],
        high=time_ct["5m high"],
        low=time_ct["5m low"],
        close=time_ct["4. close"],
    )
    layout_candle = go.Layout(
        title="[5-Minute Candlestick]"
        + " "
        + from_currency
        + "/"
        + to_currency
        + " (Last 100 Minutes)",
        showlegend=False,
        template="plotly",
    )
    data_candle = [candleplot, can_tim]
    fig_candle = go.Figure(data=data_candle, layout=layout_candle)
    fig_candle.update(layout_xaxis_rangeslider_visible=False)

    # time series plot
    # time_plot = go.Scatter(x = time_dt.index, y = time_dt["4. close"], marker = dict(color = '#17becf'), mode = "lines+markers")
    # layout = go.Layout(title = "[Intraday Plot]"+ " " + from_currency + "/"+ to_currency + " (Last 100 Time Points)")
    # data = [time_plot]
    # fig_time = go.Figure(data=data, layout=layout)

    # plot bollinger
    trace_bu = go.Scatter(
        x=time_dt.index,
        y=time_dt["bb_bbh"],
        name="Real Upper Band",
        line=dict(dash="dot"),
    )
    trace_bl = go.Scatter(
        x=time_dt.index,
        y=time_dt["bb_bbl"],
        name="Real Lower Band",
        line=dict(dash="dot"),
    )
    trace_bm = go.Scatter(
        x=time_dt.index,
        y=time_dt["bb_bbm"],
        name="Real Middle Band",
        line=dict(dash="dot"),
    )
    time_p = go.Scatter(
        x=time_dt.index,
        y=time_dt["4. close"],
        name=from_currency + to_currency,
        line=dict(color="#622569"),
    )
    layout_bol = go.Layout(
        title="[Bollinger Band (Per Minute Basis)]"
        + " "
        + from_currency
        + "/"
        + to_currency
        + " (Last 100 Time Points)",
        template="plotly",
    )

    data_bol = [trace_bu, trace_bl, trace_bm, time_p]
    fig_bol = go.Figure(data=data_bol, layout=layout_bol)

    # plot macd
    # add macd histogram color
    bpos = "#009E73"
    bneg = "#CC79A7"
    clr_hist = [bpos if x > 0 else bneg for x in time_dt["macd_hist"]]

    # macd chart
    trace_macd = go.Scatter(x=time_dt.index, y=time_dt["macd"], name="MACD")
    trace_macdS = go.Scatter(
        x=time_dt.index, y=time_dt["macd_signal"], name="MACD SIGNAL"
    )
    trace_macdH = go.Bar(
        x=time_dt.index,
        y=time_dt["macd_hist"],
        name="MACD HISTOGRAM",
        marker={"color": clr_hist},
        showlegend=False,
    )
    layout_macd = go.Layout(
        title="[MACD (Per Minute Basis)]"
        + " "
        + from_currency
        + "/"
        + to_currency
        + " (Last 100 Time Points)",
        template="plotly",
    )

    data_macd = [trace_macd, trace_macdS, trace_macdH]
    fig_MACD = go.Figure(data=data_macd, layout=layout_macd)

    # plot rsi
    trace_rsi = go.Scatter(
        x=time_dt.index, y=time_dt["rsi"], name="RSI", line=dict(color="#405d27")
    )
    layout_rsi = go.Layout(
        title="[RSI (Per Minute Basis)]"
        + " "
        + from_currency
        + "/"
        + to_currency
        + " (Last 100 Time Points)",
        template="plotly",
    )

    data_rsi = [trace_rsi]
    fig_rsi = go.Figure(data=data_rsi, layout=layout_rsi)

    # add upper band at 55
    fig_rsi.add_shape(
        # Line Horizontal
        type="line",
        x0=time_dt.index[0],
        y0=55,
        x1=time_dt.index[-1],
        y1=55,
        line=dict(color="#c94c4c", width=4, dash="dot",),
        name="Upper Band",
    )

    # add lower band at 45
    fig_rsi.add_shape(
        # Line Horizontal
        type="line",
        x0=time_dt.index[0],
        y0=45,
        x1=time_dt.index[-1],
        y1=45,
        line=dict(color="#36486b", width=4, dash="dot",),
        name="Lower Band",
    )

    fig_rsi.update_layout(showlegend=False)

    # return the outputfig.update_layout(showlegend=True)
    return (fig_candle, fig_bol, fig_rsi, fig_MACD)


# launch the app
if __name__ == "__main__":
    app.run_server(debug=False, threaded=True)

