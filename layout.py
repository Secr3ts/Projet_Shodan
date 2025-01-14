import plotly.express as px
from dash import dcc, html
from data_loader import load_csv_data, filter_french_data

DATA_FILE = "data/test_data.csv"
df = load_csv_data(DATA_FILE)
french_data = filter_french_data(df)

map_fig = px.scatter_mapbox(
    french_data,
    lat="Latitude",
    lon="Longitude",
    hover_name="City",
    hover_data={"Organization": True, "IP Address": True, "Country": False},
    color_discrete_sequence=["blue"],
    zoom=5,
    height=600,
)
map_fig.update_layout(mapbox_style="open-street-map")
map_fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

layout = html.Div(
    className="h-screen max-h-screen grid grid-rows-11 gap-2 grid-cols-6 relative overflow-hidden p-4",
    children=[
        html.Img(
            src="/assets/img/blurry_bubble_1.png",
            draggable="false",
            className="absolute -bottom-64 -left-56 select-none",
        ),
        html.Img(
            src="/assets/img/blurry_bubble_2.png",
            draggable="false",
            className="absolute top-40 -left-[400px] select-none",
        ),
        html.Img(
            src="/assets/img/blurry_bubble_3.png",
            draggable="false",
            className="absolute -bottom-28 -left-24 opacity-30 select-none",
        ),
        html.Img(
            src="/assets/img/blurry_bubble_4.png",
            draggable="false",
            className="absolute top-0 -right-[800px] select-none",
        ),
        html.H1("Carte de France des Données", className="text-3xl font-bold flex justify-end mr-16 items-center row-start-1 row-end-2 col-start-4	col-end-7"),
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Label("Informations : "),
                        html.Div(id="info-display", children="Cliquez sur un point pour voir les informations."),
                    ],
                    className="gradient-content rounded",
                ),
            ],
            className="gradient-box row-start-2 row-end-12 col-start-1 col-end-3 rounded-md",
        ),
        dcc.Graph(
            id="france-map",
            figure=map_fig,
            className="row-start-2 row-end-7 col-start-3 col-end-7 rounded-md shadow-md overflow-hidden",
        ),
        dcc.Graph(
            id="france-map-2",
            figure=map_fig,
            className="row-start-7 row-end-12 col-start-3 col-end-7 rounded-md shadow-md overflow-hidden",
        ),
    ]
)