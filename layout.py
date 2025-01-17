import json

import geopandas as gpd
import pandas as pd
import plotly.express as px
from dash import dcc, html


def create_layout():
    geojson_file = "data/cleaned/french_communes.geojson"
    geo_data = gpd.read_file(geojson_file)

    crime_data_file = "data/cleaned/crimes_france_2.csv"
    crime_data = pd.read_csv(crime_data_file)

    years = sorted(crime_data["Year"].unique())

    crime_summary = crime_data[crime_data["Year"] == years[0]].groupby(["City"])["Cases"].mean().reset_index()  # noqa: E501
    geo_data = geo_data.merge(
        crime_summary,
        how="left",
        left_on="libgeo",
        right_on="City",
    )
    geo_data["Cases"] = geo_data["Cases"].fillna(0)

    min_value = geo_data["Cases"].quantile(0.1)
    max_value = geo_data["Cases"].quantile(0.9)

    map_fig_crime = px.choropleth_mapbox(
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
    ).update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, uirevision=True)

    camera_data = []
    with open("data/backup/raw/shodan_camera_fr.json", "r") as f:
        for line in f:
            camera_data.append(json.loads(line.strip()))

    camera_locations = pd.DataFrame(
        [
            {
                "City": camera.get("location", {}).get("city", "Unknown"),
                "Latitude": camera.get("location", {}).get("latitude"),
                "Longitude": camera.get("location", {}).get("longitude"),
                "IP": camera.get("ip_str", "Unknown"),
                "Organization": camera.get("org", "Unknown"),
            }
            for camera in camera_data
        ],
    )

    map_fig_camera = px.scatter_mapbox(
        camera_locations,
        lat="Latitude",
        lon="Longitude",
        hover_name="City",
        hover_data=["IP", "Organization"],
        mapbox_style="open-street-map",
        zoom=5,
        center={"lat": 46.603354, "lon": 1.888334},
        opacity=0.8,
    )
    map_fig_camera.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    return html.Div(
        className="h-screen max-h-screen grid grid-rows-12 gap-2 grid-cols-6 relative overflow-hidden p-4",
        children=[
            html.H1(
                "Carte des Crimes et Caméras en France",
                className="text-3xl font-bold flex justify-end mr-16 items-center row-start-1 row-end-2 col-start-3 col-end-7 z-1",
            ),
            html.Div(
                children=[
                    html.Div(
                        children=[
                            html.Label("Informations. (WIP)"),
                        ],
                        className="gradient-content rounded",
                    ),
                ],
                className="gradient-box row-start-2 row-end-13 col-start-1 col-end-3 rounded-md z-1",
            ),
            dcc.RadioItems(
                id='year-radio',
                options=[{"label": str(year), "value": year} for year in years],
                value=years[0],
                inline=True,
                className="row-start-2 row-end-3 col-start-3 col-end-7 z-1 flex items-center gap-2",
            ),
            html.Div(
                children=[
                    dcc.Loading(
                        id="loading-crime-map",
                        type="circle",
                        children=dcc.Graph(
                            id="france-map-crime",
                            figure=map_fig_crime,
                            className="w-full h-full rounded-md shadow-md overflow-hidden z-1",
                        ),
                        className="w-full h-full",
                    ),
                ],
                className="map-container row-start-3 row-end-8 col-start-3 col-end-7 flex items-center justify-center",
            ),
            html.Div(
                children=[
                    dcc.Loading(
                        id="loading-camera-map",
                        type="circle",
                        children=dcc.Graph(
                            id="france-map-camera",
                            figure=map_fig_camera,
                            className="h-full w-full rounded-md shadow-md overflow-hidden z-1",
                        ),
                        className="h-full w-full",
                    ),
                ],
                className="map-container row-start-8 row-end-13 col-start-3 col-end-7 flex items-center justify-center",
            ),
            html.Div(
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
                ],
                className="-z-[1]",
            ),
        ],
    )
