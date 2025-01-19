"""The module handles the callbacks and data processing for the map visualization page.

It provides functionality for loading crime data, computing crime summaries,
and preparing geographical data for visualization across different French regions.
Contains callback registrations for interactive map updates and data filtering.
"""

import geopandas as gpd
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output

REGION_CODES = {
    "84": "ARA",  # Auvergne-Rhône-Alpes
    "27": "BFC",  # Bourgogne-Franche-Comté
    "53": "BRE",  # Bretagne
    "24": "CVL",  # Centre-Val de Loire
    "94": "COR",  # Corse
    "44": "GES",  # Grand Est
    "32": "HDF",  # Hauts-de-France
    "11": "IDF",  # Île-de-France
    "28": "NOR",  # Normandie
    "75": "NAQ",  # Nouvelle-Aquitaine
    "76": "OCC",  # Occitanie
    "52": "PDL",  # Pays de la Loire
    "93": "PAC",  # Provence-Alpes-Côte d'Azur
}

START_YEAR = 2016
END_YEAR = 2023

def load_data(
    selected_year: int,
) -> tuple[gpd.GeoDataFrame, pd.DataFrame, pd.DataFrame]:
    geojson_file = "data/cleaned/french_communes.geojson"
    geo_data = gpd.read_file(geojson_file)

    crime_data = pd.read_csv("data/cleaned/crimes_france_2.csv")
    year_crime_data = crime_data[crime_data["Year"] == selected_year]

    city_dept_mapping = pd.DataFrame({
        "City": geo_data["libgeo"],
        "dep": geo_data["dep"],
        "reg": geo_data["reg"],
    }).drop_duplicates()

    return geo_data, year_crime_data, city_dept_mapping


def compute_crime_summary(
    year_crime_data: pd.DataFrame,
    city_dept_mapping: pd.DataFrame,
    view_type: str,
) -> any:
    crime_data_with_regions = year_crime_data.merge(
        city_dept_mapping,
        on="City",
        how="left",
    )

    group_by_col = "reg" if view_type == "regions" else "dep"
    crime_summary = crime_data_with_regions.groupby(group_by_col).agg({
        "Cases": "sum",
        "POP": "sum",
    }).reset_index()

    crime_summary["Crime_Rate"] = (crime_summary["Cases"] / crime_summary["POP"]) * 100
    return crime_summary


def prepare_geo_data(
    geo_data: gpd.GeoDataFrame,
    crime_summary: pd.DataFrame,
    view_type: str,
) -> gpd.GeoDataFrame:
    """Préparer les données géographiques pour la visualisation."""
    group_by_col = "reg" if view_type == "regions" else "dep"
    current_geo_data = geo_data.dissolve(by=group_by_col, aggfunc="first").reset_index()
    current_geo_data = current_geo_data.merge(
        crime_summary,
        on=group_by_col,
        how="left",
    )

    if view_type == "regions":
        current_geo_data["reg_code"] = current_geo_data["reg"].map(REGION_CODES)
        hover_name = "reg_code"
    else:
        hover_name = group_by_col

    hover_data = {
        "Crime_Rate": ":.3f",
        "Cases": True,
        "POP": True,
        "reg": view_type == "regions",
        "dep": view_type == "departements",
    }

    current_geo_data["Crime_Rate"] = current_geo_data["Crime_Rate"].fillna(0)
    current_geo_data["Cases"] = current_geo_data["Cases"].fillna(0)
    current_geo_data["POP"] = current_geo_data["POP"].fillna(0)

    return current_geo_data, hover_name, hover_data


def update_map_callback(
    selected_year: int,
    view_type: str,
) -> go.Figure:
    geo_data, year_crime_data, city_dept_mapping = load_data(selected_year)

    if view_type == "communes":
        crime_summary = year_crime_data.groupby(["City"])[["Cases", "POP"]].mean().reset_index()  # noqa: E501
        crime_summary["Crime_Rate"] = (crime_summary["Cases"] / crime_summary["POP"]) * 100  # noqa: E501
        current_geo_data = geo_data.merge(
            crime_summary,
            how="left",
            left_on="libgeo",
            right_on="City",
        )
        current_geo_data["Crime_Rate"] = current_geo_data["Crime_Rate"].fillna(0)
        current_geo_data["Cases"] = current_geo_data["Cases"].fillna(0)
        current_geo_data["POP"] = current_geo_data["POP"].fillna(0)

        hover_name = "libgeo"
        hover_data = {
            "Crime_Rate": ":.3f",
            "Cases": True,
            "POP": True,
        }
    else:
        crime_summary = compute_crime_summary(year_crime_data, city_dept_mapping, view_type)  # noqa: E501
        current_geo_data, hover_name, hover_data = prepare_geo_data(geo_data, crime_summary, view_type)  # noqa: E501

    crime_rates = current_geo_data["Crime_Rate"].dropna()
    if len(crime_rates) > 0:
        min_value = crime_rates.quantile(0.1)
        max_value = crime_rates.quantile(0.9)
    else:
        min_value = 0
        max_value = 100

    fig = px.choropleth_mapbox(
        current_geo_data,
        geojson=current_geo_data.geometry,
        locations=current_geo_data.index,
        color="Crime_Rate",
        color_continuous_scale=["#00ff00", "#ffff00", "#ff0000"],
        range_color=(min_value, max_value),
        hover_name=hover_name,
        hover_data=hover_data,
        labels={
            "Crime_Rate": "Taux de criminalité (%)",
            "Cases": "Nombre de cas",
            "POP": "Population",
            "dep": "Département",
            "reg": "Région",
            "reg_code": "Code Région",
        },
        mapbox_style="open-street-map",
        zoom=4.5,
        center={"lat": 46.603354, "lon": 2.888334},
        opacity=0.6,
    )

    fig.update_layout(
        margin={"r": 0, "t": 30, "l": 0, "b": 0},
        title=f"Données pour l'année {selected_year}",
        title_x=0.5,
    )

    return fig


def update_statistics_callback(selected_year: int) -> tuple[str, str, str, str]:
    geo_data, year_crime_data, _ = load_data(selected_year)

    city_region_mapping = pd.DataFrame({
        "City": geo_data["libgeo"],
        "reg": geo_data["reg"],
    }).drop_duplicates()

    crime_data_with_regions = year_crime_data.merge(
        city_region_mapping,
        on="City",
        how="left",
    )

    total_crimes = int(year_crime_data["Cases"].sum())

    total_cases = year_crime_data["Cases"].sum()
    total_pop = year_crime_data["POP"].sum()
    avg_rate = (total_cases / total_pop) * 100 if total_pop > 0 else 0

    region_stats = crime_data_with_regions.groupby("reg").agg({
        "Cases": "sum",
        "POP": "sum",
    }).reset_index()

    region_stats["Crime_Rate"] = (region_stats["Cases"] / region_stats["POP"]) * 100

    worst_region_idx = region_stats["Crime_Rate"].idxmax()
    worst_region = region_stats.loc[worst_region_idx]

    worst_region_code = REGION_CODES.get(str(worst_region["reg"]), str(worst_region["reg"]))  # noqa: E501

    return (
        f"{total_crimes:,}",
        f"{avg_rate:.2f}%",
        worst_region_code,
        f"Taux: {worst_region['Crime_Rate']:.2f}%",
    )


def update_comparison_chart_callback(_: any) -> go.Figure:
    crime_data = pd.read_csv("data/cleaned/crimes_france_2.csv")
    yearly_crimes = crime_data.groupby("Year")["Cases"].sum().reset_index()
    yearly_crimes = yearly_crimes[(yearly_crimes["Year"] >= START_YEAR) & (yearly_crimes["Year"] <= END_YEAR)]  # noqa: E501

    camera_data = pd.read_csv("data/cleaned/osm_cleaned.csv", names=["Lat", "Long-", "Timestamp"])  # noqa: E501
    camera_data["Timestamp"] = pd.to_datetime(camera_data["Timestamp"], errors="coerce")
    camera_data["Year"] = camera_data["Timestamp"].dt.year

    no_date_cameras = camera_data["Timestamp"].isna().sum()

    yearly_cameras = []
    for year in range(START_YEAR, END_YEAR + 1):
        cameras_until_year = camera_data[
            (camera_data["Year"].notna()) &
            (camera_data["Year"] <= year)
        ].shape[0]

        total_cameras = cameras_until_year + no_date_cameras

        yearly_cameras.append({
            "Year": year,
            "Cameras": total_cameras,
        })

    yearly_cameras = pd.DataFrame(yearly_cameras)

    merged_data = yearly_crimes.merge(yearly_cameras, on="Year")

    merged_data["Crimes_per_100_Cameras"] = (merged_data["Cases"] / merged_data["Cameras"]) * 100  # noqa: E501

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=merged_data["Year"],
        y=merged_data["Crimes_per_100_Cameras"],
        name="Crimes pour 100 caméras",
        line={"color": "purple", "width": 2},
        mode="lines+markers",
    ))

    fig.update_layout(
        title="Évolution du nombre de crimes pour 100 caméras en France",
        xaxis_title="Année",
        yaxis_title="Nombre de crimes pour 100 caméras",
        template="plotly_white",
        hovermode="x unified",
    )

    return fig


def update_camera_evolution_callback(_: any) -> go.Figure:
    try:
        camera_data = pd.read_csv("data/cleaned/osm_cleaned.csv", names=["Lat", "Long-", "Timestamp"])  # noqa: E501
        camera_data["Timestamp"] = pd.to_datetime(camera_data["Timestamp"], errors="coerce")  # noqa: E501
        camera_data["Year"] = camera_data["Timestamp"].dt.year

        no_date_cameras = camera_data["Timestamp"].isna().sum()

        yearly_cameras = []
        for year in range(START_YEAR, END_YEAR + 1):
            cameras_until_year = camera_data[
                (camera_data["Year"].notna()) &
                (camera_data["Year"] <= year)
            ].shape[0]

            total_cameras = cameras_until_year + no_date_cameras

            yearly_cameras.append({
                "Year": year,
                "Cameras": total_cameras,
            })

        yearly_cameras = pd.DataFrame(yearly_cameras)

        fig = px.bar(
            yearly_cameras,
            x="Year",
            y="Cameras",
            title="Évolution du nombre de caméras en France",
            labels={"Cameras": "Nombre de caméras", "Year": "Année"},
            color_discrete_sequence=["#00CC96"],
        )

        fig.update_layout(
            xaxis_tickangle=-45,
            showlegend=False,
            margin={"r": 20, "t": 40, "l": 20, "b": 20},
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )

        fig.update_traces(
            marker_line_color="#009973",
            marker_line_width=1.5,
            opacity=0.8,
        )
    except (pd.errors.EmptyDataError, pd.errors.DatabaseError, ValueError, KeyError) as e:  # noqa: E501
        print(f"Error in update_camera_evolution - Data processing failed: {e!s}")
        return go.Figure()
    else:
        return fig


def update_crime_evolution_callback(_: any) -> go.Figure:
    try:
        crime_data = pd.read_csv("data/cleaned/crimes_france_2.csv")
        yearly_crimes = crime_data.groupby("Year")["Cases"].sum().reset_index()
        yearly_crimes = yearly_crimes[yearly_crimes["Year"].between(START_YEAR, END_YEAR)]  # noqa: E501

        fig = px.bar(
            yearly_crimes,
            x="Year",
            y="Cases",
            title="Évolution du nombre de crimes en France",
            labels={"Cases": "Nombre de crimes", "Year": "Année"},
            color_discrete_sequence=["#FF6B6B"],
        )

        fig.update_layout(
            xaxis_tickangle=-45,
            showlegend=False,
            margin={"r": 20, "t": 40, "l": 20, "b": 20},
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )

        fig.update_traces(
            marker_line_color="#CC5555",
            marker_line_width=1.5,
            opacity=0.8,
        )
    except (ValueError, pd.errors.EmptyDataError) as e:
        print(f"Error in update_crime_evolution - Invalid or empty data: {e}")
        return go.Figure()
    else:
        return fig


def register_callbacks(app: any) -> None:
    """Register all callbacks for the map page."""
    app.callback(
        Output("france-map-crime", "figure"),
        [Input("year-radio", "value"),
         Input("view-type-radio", "value")],
    )(update_map_callback)

    app.callback(
        [Output("total-crimes", "children"),
         Output("avg-crime-rate", "children"),
         Output("worst-region", "children"),
         Output("worst-region-rate", "children")],
        [Input("year-radio", "value")],
    )(update_statistics_callback)

    app.callback(
        Output("comparison-chart", "figure"),
        Input("year-radio", "value"),
    )(update_comparison_chart_callback)

    app.callback(
        Output("camera-evolution-chart", "figure"),
        [Input("year-radio", "value")],
    )(update_camera_evolution_callback)

    app.callback(
        Output("crime-evolution-chart", "figure"),
        [Input("year-radio", "value")],
    )(update_crime_evolution_callback)
