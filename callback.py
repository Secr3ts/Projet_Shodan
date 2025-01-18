import geopandas as gpd  # noqa: D100
import pandas as pd
import plotly.express as px
from dash import Input, Output


def register_callbacks(app) -> None:  # noqa: ANN001
    @app.callback(
        Output("france-map-crime", "figure"),
        [Input("year-radio", "value"),
         Input("view-type-radio", "value")],
    )
    def update_map(selected_year: int, view_type: str) -> any:
        geojson_file = "data/cleaned/french_communes.geojson"
        geo_data = gpd.read_file(geojson_file)

        crime_data = pd.read_csv("data/cleaned/crimes_france_2.csv")

        year_crime_data = crime_data[crime_data["Year"] == selected_year]

        if view_type == "communes":
            crime_summary = year_crime_data.groupby(["City"],)[["Cases", "POP"]].mean().reset_index()  # noqa: E501
            crime_summary["Crime_Rate"] = (crime_summary["Cases"] / crime_summary["POP"]) * 100  # noqa: E501
            current_geo_data = geo_data.merge(
                crime_summary,
                how="left",
                left_on="libgeo",
                right_on="City",
            )
            hover_name = "libgeo"
        else:
            city_dept_mapping = pd.DataFrame({
                "City": geo_data["libgeo"],
                "dep": geo_data["dep"],
            }).drop_duplicates()

            crime_data_with_dept = year_crime_data.merge(
                city_dept_mapping,
                on="City",
                how="left",
            )
            crime_summary = crime_data_with_dept.groupby("dep").agg({
                "Cases": "sum",
                "POP": "sum"
            }).reset_index()

            crime_summary["Crime_Rate"] = (crime_summary["Cases"] / crime_summary["POP"]) * 100  # noqa: E501

            current_geo_data = geo_data.dissolve(by="dep", aggfunc="first").reset_index()  # noqa: E501

            current_geo_data = current_geo_data.merge(
                crime_summary,
                on="dep",
                how="left",
            )
            hover_name = "dep"

        current_geo_data["Crime_Rate"] = current_geo_data["Crime_Rate"].fillna(0)
        current_geo_data["Cases"] = current_geo_data["Cases"].fillna(0)
        current_geo_data["POP"] = current_geo_data["POP"].fillna(0)

        min_value = current_geo_data["Crime_Rate"].quantile(0.1)
        max_value = current_geo_data["Crime_Rate"].quantile(0.9)

        fig = px.choropleth_mapbox(
            current_geo_data,
            geojson=current_geo_data.geometry,
            locations=current_geo_data.index,
            color="Crime_Rate",
            color_continuous_scale=["#00ff00", "#ffff00", "#ff0000"],
            range_color=(min_value, max_value),
            hover_name=hover_name,
            hover_data={
                "Crime_Rate": ":.3f",
                "Cases": True,
                "POP": True,
                "dep": True
            },
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
        )
        fig.update_layout(
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            uirevision=True,
        )

        return fig

    @app.callback(
        Output("click-data", "children"),
        Input("france-map-crime", "clickData"),
    )
    def display_click_data(click_data) -> str:  # noqa: ANN001
        if click_data is None:
            return "Cliquez sur une zone pour voir les détails"

        point_data = click_data["points"][0]
        return f"Zone : {point_data['hovertext']}, Taux de criminalité : {point_data['customdata'][0]:.2f}%"  # noqa: E501
