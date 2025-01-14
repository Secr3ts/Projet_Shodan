from dash import Dash
from layout import layout
from callback import register_callbacks

app = Dash(__name__)

app.layout = layout

register_callbacks(app)

if __name__ == "__main__":
    app.run_server(debug=True)