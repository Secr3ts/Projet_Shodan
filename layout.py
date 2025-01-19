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

    crime_summary = crime_data[crime_data["Year"] == years[0]].groupby(["City"])[["Cases", "POP"]].mean().reset_index()  # noqa: E501
    crime_summary["Crime_Rate"] = (crime_summary["Cases"] / crime_summary["POP"]) * 100
    geo_data = geo_data.merge(
        crime_summary,
        how="left",
        left_on="libgeo",
        right_on="City",
    )
    geo_data["Crime_Rate"] = geo_data["Crime_Rate"].fillna(0)
    geo_data["Cases"] = geo_data["Cases"].fillna(0)
    geo_data["POP"] = geo_data["POP"].fillna(0)

    min_value = geo_data["Crime_Rate"].quantile(0.1)
    max_value = geo_data["Crime_Rate"].quantile(0.9)

    map_fig_crime = px.choropleth_mapbox(
        geo_data,
        geojson=geo_data.geometry,
        locations=geo_data.index,
        color="Crime_Rate",
        color_continuous_scale=["#00ff00", "#ffff00", "#ff0000"],
        range_color=(min_value, max_value),
        hover_name="libgeo",
        hover_data={"Crime_Rate": ":.3f","Cases": True,"POP": True,"dep": True},
        labels={
            "Crime_Rate": "Taux de criminalité (%)",
            "Cases": "Nombre de cas",
            "POP": "Population",
            "dep": "Département",
        },
        mapbox_style="open-street-map",
        zoom=5,
        center={"lat": 46.603354, "lon": 1.888334},
        opacity=0.6,
    ).update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, uirevision=True)

    crime_data = pd.read_csv("data/cleaned/crimes_france_2.csv")

    total_population = crime_data[crime_data['Year'] == 2023]['POP'].sum()

    camera_locations = pd.read_csv("data/cleaned/shodan_camera_fr.csv")
    total_cameras = len(camera_locations)

    camera_coverage = round((total_cameras * 100000) / total_population, 2)

    map_fig_camera = px.scatter_mapbox(
        camera_locations,
        lat="Latitude",
        lon="Longitude",
        hover_name="City",
        hover_data={
            "IP": True,
            "Org": True,
            "Region": True,
            "Timestamp": True,
            "Domains": True
        },
        mapbox_style="open-street-map",
        zoom=5,
        center={"lat": 46.603354, "lon": 1.888334},
        opacity=0.8,
        color_discrete_sequence=["blue"],
    )
    map_fig_camera.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    region_camera_counts = camera_locations['Region'].value_counts()
    most_cameras_region = region_camera_counts.index[0]
    most_cameras_count = region_camera_counts.iloc[0]

    return html.Div(
        className="grid grid-rows-[50px_600px_50px_600px_600px_600px] gap-4 grid-cols-5 relative overflow-hidden p-4",
        children=[
            html.H1(
                "Carte des Crimes et Caméras en France",
                className="text-3xl font-bold text-center col-span-5",
            ),
            html.Div(
                children=[
                    dcc.Loading(
                        id="loading-crime-map",
                        type="circle",
                        children=dcc.Graph(
                            id="france-map-crime",
                            figure=map_fig_crime,
                            className="w-full h-full rounded-md shadow-md overflow-hidden z-1",  # noqa: E501
                        ),
                        className="w-full h-full flex items-center",
                    ),
                ],
                className="map-container row-start-2 row-end-3 col-start-1 col-end-4 flex items-center justify-center bg-white rounded-md overflow-hidden",  # noqa: E501
            ),
            html.Div(
                children=[
                    html.Div(
                        className="absolute inset-0 bg-gradient-to-r from-blue-500 to-purple-600 opacity-75 rounded-md",  # noqa: E501
                    ),
                    html.Div(
                        className="relative p-6 text-white",
                        children=[
                            html.H2("Informations Clés", className="text-2xl font-bold mb-4"),  # noqa: E501
                            html.Div(
                                className="grid grid-rows-3 gap-4",
                                children=[
                                    html.Div(
                                        className="bg-white/20 p-4 rounded-lg",
                                        children=[
                                            html.H3("Total des Crimes", className="text-lg font-semibold mb-2"),  # noqa: E501
                                            html.P(id="total-crimes", className="text-3xl font-bold"),  # noqa: E501
                                            html.P("en France", className="text-sm opacity-75"),  # noqa: E501
                                        ]
                                    ),
                                    html.Div(
                                        className="bg-white/20 p-4 rounded-lg",
                                        children=[
                                            html.H3("Taux Moyen", className="text-lg font-semibold mb-2"),  # noqa: E501
                                            html.P(id="avg-crime-rate", className="text-3xl font-bold"),  # noqa: E501
                                            html.P("pour 100 habitants", className="text-sm opacity-75"),  # noqa: E501
                                        ]
                                    ),
                                    html.Div(
                                        className="bg-white/20 p-4 rounded-lg",
                                        children=[
                                            html.H3("Région la Plus Touchée", className="text-lg font-semibold mb-2"),  # noqa: E501
                                            html.P(id="worst-region", className="text-3xl font-bold"),  # noqa: E501
                                            html.P(id="worst-region-rate", className="text-sm opacity-75"),  # noqa: E501
                                        ]
                                    )
                                ]
                            )
                        ]
                    )
                ],
                className="row-start-2 row-end-3 col-start-4 col-end-6 bg-white rounded-md shadow-md relative overflow-hidden",  # noqa: E501
            ),
            dcc.RadioItems(
                id="view-type-radio",
                options=[
                    {"label": "Communes", "value": "communes"},
                    {"label": "Départements", "value": "departements"},
                    {"label": "Régions", "value": "regions"}
                ],
                value="communes",
                inline=True,
                className="row-start-3 row-end-4 col-start-4 col-end-6 z-1 flex items-center gap-2",  # noqa: E501
            ),
            dcc.RadioItems(
                id="year-radio",
                options=[{"label": str(year), "value": year} for year in years],
                value=years[0],
                inline=True,
                className="row-start-3 row-end-4 col-start-1 col-end-2 z-1 flex items-center gap-2",  # noqa: E501
            ),
            html.Div(
                children=[
                    html.Div(
                        className="absolute inset-0 bg-gradient-to-r from-blue-500 to-purple-600 opacity-75 rounded-md",  # noqa: E501
                    ),
                    html.Div(
                        className="relative p-6 text-white",
                        children=[
                            html.H2("Informations Clés", className="text-2xl font-bold mb-4"),  # noqa: E501
                            html.Div(
                                className="grid grid-rows-3 gap-4",
                                children=[
                                    html.Div(
                                        className="bg-white/20 p-4 rounded-lg",
                                        children=[
                                            html.H3("Total Caméras", className="text-lg font-semibold mb-2"),  # noqa: E501
                                            html.P(total_cameras, id="total-cameras", className="text-3xl font-bold"),  # noqa: E501
                                            html.P("en France", className="text-sm opacity-75"),  # noqa: E501
                                        ]
                                    ),
                                    html.Div(
                                        className="bg-white/20 p-4 rounded-lg",
                                        children=[
                                            html.H3("Région la Plus Surveillée", className="text-lg font-semibold mb-2"),  # noqa: E501
                                            html.P(most_cameras_region, id="most-cameras-region", className="text-3xl font-bold"),  # noqa: E501
                                            html.P(most_cameras_count, id="most-cameras-count", className="text-sm opacity-75"),  # noqa: E501
                                        ]
                                    ),
                                    html.Div(
                                        className="bg-white/20 p-4 rounded-lg",
                                        children=[
                                            html.H3("Taux de Couverture", className="text-lg font-semibold mb-2"),  # noqa: E501
                                            html.P(camera_coverage, id="camera-coverage", className="text-3xl font-bold"),  # noqa: E501
                                            html.P("caméras/100k habitants", className="text-sm opacity-75"),  # noqa: E501
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
                className="row-start-4 row-end-5 col-start-1 col-end-3 bg-white rounded-md shadow-md relative overflow-hidden",  # noqa: E501
            ),
            html.Div(
                children=[
                    dcc.Loading(
                        id="loading-camera-map",
                        type="circle",
                        children=dcc.Graph(
                            id="france-map-camera",
                            figure=map_fig_camera,
                            className="h-full w-full rounded-md shadow-md overflow-hidden z-1",  # noqa: E501
                        ),
                        className="h-full w-full",
                    ),
                ],
                className="map-container row-start-4 row-end-5 col-start-3 col-end-6 flex items-center justify-center bg-white rounded-md overflow-hidden",  # noqa: E501
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
                        className="absolute -top-[528px] -right-[14.75rem] opacity-30 select-none",  # noqa: E501
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
