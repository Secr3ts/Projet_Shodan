from __future__ import annotations

import json
from gzip import decompress
from math import ceil
from os import getenv
from pathlib import Path
import sys
from typing import Callable

from pandas import DataFrame, read_csv, to_numeric
from requests import RequestException, get, head
from shodan import APIError, Shodan


def get_data(
    shodan_clients: list[Shodan],
    raw_path: Path = Path("./", "data", "raw"),
) -> None:
    create_directories()

    if "dev" in getenv("ENV"):
        get_shodan_data(shodan_clients)
    v_commune_path: Path = download_data(
        "https://www.insee.fr/fr/statistiques/fichier/7766585/v_commune_2024.csv",
        raw_path / "v_commune_2024.csv",
    )
    crimes_france_path: Path = download_data(
        "https://static.data.gouv.fr/resources/bases-statistiques-communale-departementale-et-regionale-de-la-delinquance-enregistree-par-la-police-et-la-gendarmerie-nationales/20240718-150309/donnee-data.gouv-2023-geographie2024-produit-le2024-07-05.csv.gz",
        raw_path / "crimes_france_2.csv.gz",
        alternate_url="https://www.data.gouv.fr/fr/datasets/r/3f51212c-f7d2-4aec-b899-06be6cdd1030",
        callback=decompress_gz,
    )
    french_deps_path: Path = download_data(
        "https://static.data.gouv.fr/resources/contours-des-communes-de-france-simplifie-avec-regions-et-departement-doutre-mer-rapproches/20220219-095144/a-com2022.json",
        raw_path / "french_communes.geojson",
        alternate_url="https://www.data.gouv.fr/fr/datasets/r/fb3580f6-e875-408d-809a-ad22fc418581",
    )
    files_raw = [crimes_france_path, french_deps_path]
    for file in files_raw:
        clean_data(file, v_commune_path)
    cleanup_data(Path("./", "data", "raw"))


def create_directories() -> None:
    data_path = Path("./", "data")
    if not data_path.exists():
        data_path.mkdir()
    raw_path = data_path / "raw"
    cleaned_path = data_path / "cleaned"
    if not raw_path.exists():
        raw_path.mkdir()
    if not cleaned_path.exists():
        cleaned_path.mkdir()
    for entry in raw_path.iterdir():
        if entry.is_file():
            entry.unlink()
    for entry in cleaned_path.iterdir():
        if entry.is_file():
            entry.unlink()


def decompress_gz(path: Path) -> Path:
    with path.open("rb") as gz:
        compressed = gz.read()
        decompressed = decompress(compressed)
        decompressed_path = path.with_suffix("")
        with decompressed_path.open("wb") as decompressed_file:
            decompressed_file.write(decompressed)
    path.unlink()
    return decompressed_path


def clean_data(file: Path, french_cities: Path) -> None:
    match file.suffix:
        case ".csv":
            clean_csv_data(file, french_cities)
        case ".geojson":
            move_geojson_file(file)


def clean_csv_data(file: Path, french_cities: Path) -> None:
    # Process CSV Data
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
        "LOG": float,  # Using float as scientific notation is present
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
    merged_df = merged_df.drop(
        columns=["COM", "NCCENR", "POP", "millPOP", "LOG", "millLOG", "tauxpourmille"],
    )
    merged_df = merged_df.rename(
        columns={"CODGEO_2024": "City", "annee": "Year", "faits": "Cases"},
    )
    merged_df.to_csv(Path("./", "data", "cleaned", file.parts[-1]), index=False)


def move_geojson_file(file: Path) -> None:
    file_dest = Path("./", "data", "cleaned", file.parts[-1])
    file.rename(file_dest)


def cleanup_data(directory: Path) -> None:
    for file in directory.iterdir():
        if file.is_file():
            file.unlink()


def download_data(
    url: str,
    save_path: Path,
    alternate_url: str | None = None,
    callback: Callable | None = None,
) -> Path:
    try:
        check = head(url)
        with get(url if check.ok else alternate_url, stream=True) as r:
            r.raise_for_status()
            with save_path.open(mode="wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            if callback:
                return callback(save_path)
            return save_path
    except (RequestException, APIError) as e:
        print(e)
        # fallback to /data/backup/
        backup_path = Path("./", "data", "backup", save_path.name)
        if backup_path.exists():
            return backup_path
        print(f"Backup file {backup_path} not found.")


MAX_TRIES = 0
RESULTS_LIMIT = 100  # Adjust this value to limit the number of results per page


def get_shodan_data(
    shodan_clients: list[Shodan],
    tries: int = 1,
    start_page: int = 1,
) -> None:
    if tries > MAX_TRIES:
        print("max tries reached, Falling back to the JSON")
        fallback_to_json()
        return
    shodan = shodan_clients[0]
    # 10 results per page, 1 query credit per 100 results, 10 pages per api full api key
    try:
        shodan = shodan_clients[0]
        count = shodan.count("camera country:fr before:2024-01-01")

        # 100 results per page
        total_pages = ceil(count["total"] / RESULTS_LIMIT)
        cleaned_data = []

        for i in range(start_page, total_pages + 1):
            try:
                result = shodan.search("camera country:fr before:2024-01-01", page=i)

                if "matches" not in result:
                    print("No matches. Falling back to the JSON")
                    fallback_to_json()
                    break

                cleaned_data.extend(clean_shodan_result(result))
            except APIError as e:
                print(f"APIError: {e}")
                if "query credits" in str(e).lower():
                    if len(shodan_clients) > 1:
                        shodan_clients.pop(0)
                        print("Switching to next API key")
                        get_shodan_data(shodan_clients, tries, start_page=i)
                        return
                    print("No more API keys available")
                    fallback_to_json()
                    return

        # Convert cleaned data to DataFrame
        shodan_df = DataFrame(cleaned_data)
        shodan_df.to_csv(
            Path("./", "data", "cleaned", "shodan_camera_fr.csv"),
            mode="a",
            header=False,
        )
    except APIError as e:
        print(e)
        get_shodan_data(shodan_clients, tries + 1, start_page)


def fallback_to_json() -> None:
    try:
        cleaned_data = []
        with Path(
            "./",
            "data",
            "backup",
            "raw",
            "shodan_camera_fr.json",
        ).open(mode="r") as f:
            lines = f.readlines()
            for line in lines:
                data = json.loads(line)
                cleaned_data.extend(clean_shodan_result(data, fallback=True))
            shodan_df = DataFrame(
                cleaned_data,
                columns=[
                    "IP",
                    "City",
                    "Region",
                    "Latitude",
                    "Longitude",
                    "Timestamp",
                    "Org",
                    "Domains",
                ],
            )
            shodan_df.to_csv(
                Path("./", "data", "cleaned", "shodan_camera_fr.csv"),
                index=False,
            )
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Failed to load fallback JSON: {e}")


def clean_shodan_result(shodan_result: dict, *, fallback: bool = False) -> list:
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
