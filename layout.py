import geopandas as gpd
import pandas as pd
import plotly.express as px
from dash import dcc, html


def create_layout():
    geojson_file = "data/cleaned/french_communes.geojson"
    geo_data = gpd.read_file(geojson_file)

    crime_data_file = "data/cleaned/crimes_france_2.csv"
    crime_data = pd.read_csv(crime_data_file)

    crime_summary = crime_data.groupby("City")["Cases"].mean().reset_index()
    geo_data = geo_data.merge(
        crime_summary,
        how="left",
        left_on="libgeo",
        right_on="City",
    )
    geo_data["Cases"] = geo_data["Cases"].fillna(0)

    min_value = geo_data["Cases"].quantile(0.1)
    max_value = geo_data["Cases"].quantile(0.9)

    map_fig = px.choropleth_mapbox(
        geo_data,
        geojson=geo_data.geometry,
        locations=geo_data.index,
        color="Cases",
        color_continuous_scale=["#00ff00", "#ffff00", "#ff0000"],
        range_color=(min_value, max_value),
        hover_name="libgeo",
        hover_data={"Cases": True, "City": False},
        mapbox_style="open-street-map",
        zoom=5,
        center={"lat": 46.603354, "lon": 1.888334},
        opacity=0.6,
    )

    map_fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    years = sorted(crime_data["Year"].unique())

    return html.Div(
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
            html.H1(
                "Carte des Crimes en France",
                className="text-3xl font-bold flex justify-end mr-16 items-center row-start-1 row-end-2 col-start-4 col-end-7",
            ),
            html.Div(
                children=[
                    html.Div(
                        children=[
                            html.Label("Sélectionnez une année :"),
                            dcc.Dropdown(
                                id="year-selector",
                                options=[{"label": str(year), "value": year} for year in years],
                                value=years[0],
                            ),
                            html.Label("Informations : "),
                            html.Div(
                                id="info-display",
                                children="Cliquez sur une commune pour voir les informations."
                            ),
                        ],
                        className="gradient-content rounded",
                    ),
                ],
                className="gradient-box row-start-2 row-end-12 col-start-1 col-end-3 rounded-md",
            ),
            dcc.Graph(
                id="france-map",
                figure=map_fig,
                className="row-start-2 row-end-12 col-start-3 col-end-7 rounded-md shadow-md overflow-hidden",
            ),
        ],
    )
