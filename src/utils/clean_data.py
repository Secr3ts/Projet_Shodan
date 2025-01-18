"""clean_data module provides functions to clean the data needed for the dashboard."""
from __future__ import annotations

from json import JSONDecodeError, loads
from pathlib import Path
from re import compile as recompile

from pandas import DataFrame, read_csv, to_numeric

from src.utils.utils import move_geojson_file


def clean_data(file: Path, french_cities: Path) -> None:
    """Clean the base CSV/GeoJSON data.

    :param Path file: File to clean
    :param Path french_cities: File used to cross-reference cities with file.
    """
    match file.suffix:
        case ".csv":
            clean_csv_data(file, french_cities)
        case ".geojson":
            move_geojson_file(file)

def clean_csv_data(file: Path, french_cities: Path) -> None:
    """Clean the crimes csv.

    :param Path file: File to clean
    :param Path french_cities: File used to cross-reference cities with file.
    """
    # DataTypes for CSV
    dtype = {
        "CODGEO_2024": str,
        "annee": int,
        "classe": str,
        "unité.de.compte": str,
        "valeur.publiée": str,
        "tauxpourmille": object,
        "faits": float,
        "complementinfoval": str,
        "complementinfotaux": str,
        "POP": int,
        "millPOP": int,
        "LOG": object,
        "millLOG": int,
    }

    # Reads the csv
    crimes_df = read_csv(file, delimiter=";", decimal=",", dtype=dtype)
    # Convert year to int and prepend "20"
    crimes_df["annee"] = crimes_df["annee"].apply(lambda x: int(f"20{x:02d}"))
    # Handle geographical codes
    crimes_df["CODGEO_2024"] = crimes_df["CODGEO_2024"].astype(str).str.zfill(5)
    # Convert numeric columns with French decimal format
    numeric_cols = {
        "faits": float,
        "tauxpourmille": float,
        "complementinfoval": float,
        "complementinfotaux": float,
        "POP": int,
        "millPOP": int,
        "LOG": float,
        "millLOG": int,
    }

    for col, dtype in numeric_cols.items():
        if col in crimes_df.columns:
            crimes_df[col] = to_numeric(crimes_df[col], errors="coerce").astype(dtype)

    ndiff_mask = crimes_df["valeur.publiée"] == "ndiff"
    crimes_df.loc[ndiff_mask, "faits"] = crimes_df.loc[ndiff_mask, "complementinfoval"]
    crimes_df.loc[ndiff_mask, "tauxpourmille"] = crimes_df.loc[
        ndiff_mask,
        "complementinfotaux",
    ]
    cat_cols = ["classe", "unité.de.compte", "valeur.publiée"]
    crimes_df[cat_cols] = crimes_df[cat_cols].astype("category")
    crimes_df = crimes_df.drop(["complementinfoval", "complementinfotaux"], axis=1)
    crimes_df = (
        crimes_df.groupby(["CODGEO_2024", "annee"]).sum(numeric_only=True).reset_index()
    )

    # Load French cities data
    communes_cols = ["COM", "NCCENR"]
    french_cities_df = read_csv(french_cities, usecols=communes_cols)

    # Merge dataframes to replace CODGEO_2024 with NCCENR
    merged_df = crimes_df.merge(
        french_cities_df,
        left_on="CODGEO_2024",
        right_on="COM",
        how="left",
    )
    merged_df["CODGEO_2024"] = merged_df["NCCENR"]

    # Drop various unused columns
    merged_df = merged_df.drop(
        columns=["COM", "NCCENR", "millPOP", "LOG", "millLOG", "tauxpourmille"],
    )
    merged_df = merged_df.rename(
        columns={"CODGEO_2024": "City", "annee": "Year", "faits": "Cases"},
    )

    # Saves the resulting DataFrame
    merged_df.to_csv(Path("./", "data", "cleaned", file.parts[-1]), index=False)

def clean_osm_data(data: dict[any: any]) -> None:
    """Clean OpenStreetMap data.

    :param dict[any:any] data: Data retrieved from Overpass Turbo (OSM API)
    """
    osm_df = DataFrame(data)
    osm_df["tags"] = osm_df["tags"].apply(extract_date)
    osm_df = osm_df.drop(columns=["type", "id"])
    osm_df = osm_df.rename(columns={"lat": "Lat", "lon": "Long-", "tags": "Timestamp"})
    osm_df.to_csv(Path("./", "data", "cleaned", "osm_cleaned.csv"), index=False)


def extract_date(tag: any) -> str | None:
    """Extract date from given OSM metadata.

    :param tag any: Metadata to be analyzed
    """
    date_keys = ["date", "start"]
    date_pattern = recompile(r"^\d{4}-\d{2}")
    if isinstance(tag, dict):
        for key, value in tag.items():
            if any(date_key in key.lower() for date_key in date_keys):
                match = date_pattern.match(value)
                if match:
                    return match.group(0)
    elif isinstance(tag, str):
        try:
            tag_d = loads(tag.replace("'", '"'))
            for key, value in tag_d.items():
                if any(date_key in key.lower() for date_key in date_keys):
                    match = date_pattern.match(value)
                    if match:
                        return match.group(0)
        except JSONDecodeError:
            pass
    return None

def clean_shodan_result(shodan_result: dict, *, fallback: bool = False) -> list:
    """Clean shodan result.

    :param shodan_result dict: Data retrieved from shodan
    :param fallback bool: Self-explanatory
    """
    cleaned_results = []

    if fallback:
        return [
            {
                "IP": shodan_result.get("ip_str"),
                "City": shodan_result.get("location", {}).get("city"),
                "Region": shodan_result.get("location", {}).get("region_code"),
                "Longitude": shodan_result.get("location", {}).get("longitude"),
                "Latitude": shodan_result.get("location", {}).get("latitude"),
                "Timestamp": shodan_result.get("timestamp"),
                "Org": shodan_result.get("org"),
                "Domains": shodan_result.get("domains"),
            },
        ]

    for match in shodan_result.get("matches", []):
        cleaned_result = {
            "IP": match.get("ip_str"),
            "City": match.get("location", {}).get("city"),
            "Region": match.get("location", {}).get("region_code"),
            "Longitude": match.get("location", {}).get("longitude"),
            "Latitude": match.get("location", {}).get("latitude"),
            "Timestamp": match.get("timestamp"),
            "Org": match.get("org"),
            "Domains": match.get("domains"),
        }
        cleaned_results.append(cleaned_result)

    return cleaned_results
