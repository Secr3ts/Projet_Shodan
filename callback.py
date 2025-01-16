import geopandas as gpd
import pandas as pd
import plotly.express as px
from dash.dependencies import Input, Output

GEOJSON_FILE = "data/cleaned/french_communes.geojson"
geo_data = gpd.read_file(GEOJSON_FILE)

CRIME_DATA_FILE = "data/cleaned/crimes_france_2.csv"
crime_data = pd.read_csv(CRIME_DATA_FILE)

def register_callbacks(app) -> None:
    @app.callback(
        Output("france-map", "figure"),
        Input("year-selector", "value"),
    )
    def update_map(selected_year):  # noqa: ANN001, ANN202
        # Filtrer les données pour l'année sélectionnée
        filtered_data = crime_data[crime_data["Year"] == selected_year]
        crime_summary = filtered_data.groupby("City")["Cases"].mean().reset_index()
        updated_geo_data = geo_data.merge(crime_summary, how="left", left_on="libgeo", right_on="City")
        updated_geo_data["Cases"] = updated_geo_data["Cases"].fillna(0)

        # Calculer les valeurs pour la carte
        min_value = updated_geo_data["Cases"].quantile(0.1)
        max_value = updated_geo_data["Cases"].quantile(0.9)

        # Créer la figure de la carte
        map_fig = px.choropleth_mapbox(
            updated_geo_data,
            geojson=updated_geo_data.geometry,
            locations=updated_geo_data.index,
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
        return map_fig

    @app.callback(
        Output("info-display", "children"),
        Input("france-map", "clickData"),
    )
    def update_info(click_data) -> str:
        if click_data is None:
            return "Cliquez sur une commune pour voir les informations."

        point_data = click_data["points"][0]
        city = point_data.get("hovertext", "Commune inconnue")
        return f"Informations sur la commune : {city}"