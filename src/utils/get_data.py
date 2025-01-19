"""Get data from various sources then cleans them and feeds them to the dashboard."""

from __future__ import annotations

from json import JSONDecodeError
from math import ceil
from pathlib import Path
from typing import Callable

from pandas import DataFrame
from requests import RequestException, get, head
from shodan import APIError, Shodan

from src.utils.clean_data import clean_data, clean_osm_data, clean_shodan_result
from src.utils.utils import (
    cleanup_data,
    decompress_gz,
    fallback_to_json,
    setup_directories,
)


def get_data(
    shodan_clients: list[Shodan],
    raw_path: Path = Path("./", "data", "raw"),
) -> None:
    """Set the working space, get data and clean them.

    :param shodan_clients list[Shodan]: List of shodan clients (one api key per client)
    :param raw_path Path: path to save the dirty files to
    """
    setup_directories()

    get_osm_data("http://overpass-api.de/api/interpreter")

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


def download_data(
    url: str,
    save_path: Path,
    alternate_url: str | None = None,
    callback: Callable | None = None,
) -> Path:
    """Download data.

    :param url str: the url to download data from
    :param save_path Path: the files will be saved at this location
    :param alternate_url str: only used if url isn't reachable
    :param callback Callable | None: gets called after downloading
    """
    try:
        check = head(url)
        with get(url if check.ok else alternate_url or "", stream=True) as r:
            r.raise_for_status()
            with save_path.open(mode="wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            if callback:
                return callback(save_path)
    except (RequestException, APIError) as e:
        print(e)
        # fallback to /data/backup/
        backup_path = Path("./", "data", "backup", save_path.name)
        if backup_path.exists():
            return backup_path
        print(f"Backup file {backup_path} not found.")

    return save_path


MAX_TRIES = 0
RESULTS_LIMIT = 100  # Adjust this value to limit the number of results per page


def get_shodan_data(
    shodan_clients: list[Shodan],
    tries: int = 1,
    start_page: int = 1,
) -> None:
    """Try to get data from shodan API. If failing, fallbacks to the JSON.

    :param shodan_clients list[Shodan]: clients to be used to get data
    :param tries int: number of current try
    :param start_page int: will try to get data from this page on
    """
    if tries > MAX_TRIES:
        fallback_to_json(clean_shodan_result)
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
                    fallback_to_json(clean_shodan_result)
                    break

                cleaned_data.extend(clean_shodan_result(result))
            except APIError as e:
                if "query credits" in str(e).lower():
                    if len(shodan_clients) > 1:
                        shodan_clients.pop(0)
                        get_shodan_data(shodan_clients, tries, start_page=i)
                        return
                    fallback_to_json(clean_shodan_result)
                    return

        # Convert cleaned data to DataFrame
        shodan_df = DataFrame(cleaned_data)
        shodan_df.to_csv(
            Path("./", "data", "cleaned", "shodan_camera_fr.csv"),
            mode="a",
            header=False,
        )
    except APIError:
        get_shodan_data(shodan_clients, tries + 1, start_page)


def get_osm_data(endpoint_url: str) -> None:
    """Get data from OpenStreetMap.

    :param endpoint_url str: API url to get data from
    """
    query = """
    [out:json];
    area[name="France"]->.searchArea;

    // Search for nodes, ways, or relations with camera-related tags
    (
      node["man_made"="surveillance"](area.searchArea);
      node["surveillance"](area.searchArea);
      way["man_made"="surveillance"](area.searchArea);
      way["surveillance"](area.searchArea);
    );

    // Output the results
    out body;
    >;
    out skel qt;
    """

    try:
        response = get(endpoint_url, params={"data": query})
        response.raise_for_status()  # Raise an error for bad responses
        data = response.json()

        els = data.get("elements", [])

        clean_osm_data(els)
    except RequestException:
        pass
    except JSONDecodeError:
        pass
