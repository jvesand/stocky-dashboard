import dash
import os
from load_data import StockData
from dash.dependencies import Output, Input
import plotly_express as px
from time_filtering import filter_time
import pandas as pd
from layout import Layout
import dash_bootstrap_components as dbc

directory_path = os.path.dirname(__file__)
path = os.path.join(directory_path, "stocks_data")

stock_data_object = StockData(path)

# pick one stock
# print(stock_data_object.stock_dataframe("AAPL"))

symbol_dict = {"AAPL": "Apple", "NVDA": "Nvidia", "TSLA": "Tesla", "IBM": "IBM"}

# create dictionary of dataframes (dictionary of lists of dataframes)
df_dict = {
    symbol: stock_data_object.stock_dataframe(symbol) for symbol in symbol_dict
}  # dict loop takes keys, if want values do .items()

# create a Dash App
# themes: http://dash-bootstrap-components.opensource.faculty.ai/docs/themes/explorer/
# styling cheatsheet: https://hackerthemes.com/bootstrap-cheatsheet/
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.MATERIA], # looks in assets map by default
    # makes responsivity possible (different web browser sizes)
    meta_tags=[dict(name="viewport", content="width=device-width, initial-scale=1.0")],
)

server = app.server

app.layout = Layout(symbol_dict).layout()

# now have a filtered_df that can be used as Input
@app.callback(
    Output("filtered_df", "data"),
    Input("stockpicker-dropdown", "value"),
    Input("time-slider", "value"),
)
def filter_df(stock, time_index):
    # tuple unpacks a list (list of two dfs -> two dfs)
    dff_daily, dff_intraday = df_dict[stock]

    # intraday had data up to about a month: slider index 2 is 30 days
    dff = dff_intraday if time_index <= 2 else dff_daily

    days = {i: day for i, day in enumerate([1, 7, 30, 90, 365, 365 * 5])}

    # true if slider is max, else limit days to slider
    dff = dff if time_index == 6 else filter_time(dff, days=days[time_index])

    return dff.to_json()


@app.callback(
    Output("highest-value", "children"),
    Output("lowest-value", "children"),
    Input("filtered_df", "data"),
    Input("ohlc-radio", "value"),
)
def highest_lowest_value_update(json_df, ohlc):
    dff = pd.read_json(json_df)
    highest_value = dff[ohlc].max()
    lowest_value = dff[ohlc].min()
    # first goest to first output, second to second
    return f"${highest_value:.2f}", f"${lowest_value:.2f}"


@app.callback(
    Output("stock-graph", "figure"),
    Input("filtered_df", "data"),
    Input("stockpicker-dropdown", "value"),
    Input("ohlc-radio", "value"),
)
def update_graph(json_df, stock, ohlc):
    dff = pd.read_json(json_df)
    return px.line(dff, x=dff.index, y=ohlc, title=symbol_dict[stock])


if __name__ == "__main__":
    app.run_server(debug=True)
