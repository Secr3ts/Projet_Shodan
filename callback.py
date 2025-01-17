import geopandas as gpd
import pandas as pd
import plotly.express as px
from dash import Input, Output


def register_callbacks(app):
    @app.callback(
        Output("france-map-crime", "figure"),
        [Input("year-radio", "value")]
    )
    def update_map(selected_year):
        geojson_file = "data/cleaned/french_communes.geojson"
        geo_data = gpd.read_file(geojson_file)

        crime_data_file = "data/cleaned/crimes_france_2.csv"
        crime_data = pd.read_csv(crime_data_file)

        year_crime_data = crime_data[crime_data["Year"] == selected_year]
        crime_summary = year_crime_data.groupby(["City"])["Cases"].mean().reset_index()

        geo_data = geo_data.merge(
            crime_summary,
            how="left",
            left_on="libgeo",
            right_on="City",
        )
        geo_data["Cases"] = geo_data["Cases"].fillna(0)

        min_value = geo_data["Cases"].quantile(0.1)
        max_value = geo_data["Cases"].quantile(0.9)

        fig = px.choropleth_mapbox(
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
        fig.update_layout(
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            uirevision=True,
        )

        return fig

    @app.callback(
        [Input("france-map-crime", "clickData")],
    )
    def display_click_data(click_data):
        if click_data is None:
            return "Informations. (WIP) 2"

        point_data = click_data["points"][0]
        return f"Commune : {point_data['hovertext']}, Cas : {point_data['customdata'][0]:.2f}"