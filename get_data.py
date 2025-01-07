from __future__ import annotations

import json
from gzip import decompress
from math import ceil
from pathlib import Path
from typing import Callable

import pandas as pd
from requests import RequestException, get, head
from shodan import APIError, Shodan


def get_data(
    shodan: Shodan,
    raw_path: Path = Path("./", "data", "raw"),
) -> None:
    # TODO(Aloïs FOURNIER): create dirs !!!
    # get_shodan_data(shodan)
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
        clean_data(file)


def decompress_gz(path: Path) -> None:
    with path.open("rb") as gz:
        compressed = gz.read()
        decompressed = decompress(compressed)
        decompressed_path = path.with_suffix("")
        with decompressed_path.open("wb") as decompressed_file:
            decompressed_file.write(decompressed)
    path.unlink()


def clean_data(file: Path) -> None:
    match file.suffix:
        case ".csv":
            
            return
        case ".geojson":
            file_dest = Path("./", "data", "cleaned", file.parts[-1])
            file.rename(file_dest)
            return


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
                callback(save_path)
            return save_path
    except (RequestException, APIError) as e:
        print(e)
        # fallback to /data/backup/
        backup_path = Path("./", "data", "backup", save_path.name)
        if backup_path.exists():
            return backup_path
        print(f"Backup file {backup_path} not found.")


MAX_TRIES = 5


def get_shodan_data(shodan: Shodan, tries: int = 1) -> None:
    if tries > MAX_TRIES:
        print("max tries reached, Falling back to the JSON")
        fallback_to_json()
        return

    try:
        count = shodan.count("camera country:fr")

        # 100 results per page
        total_pages = ceil(count["total"] / 100)
        cleaned_data = []

        for i in range(1):
            result = shodan.search("camera country:fr", page=i)

            if "matches" not in result:
                print("No matches. Falling back to the JSON")
                fallback_to_json()
                break

            cleaned_data.extend(clean_shodan_result(result))

        # Convert cleaned data to DataFrame
        shodan_df = pd.DataFrame(cleaned_data)
        print(shodan_df)
    except APIError as e:
        print(e)
        get_shodan_data(shodan, tries + 1)


def fallback_to_json() -> None:
    try:
        with Path("./", "data", "backup", "shodan_camera_fr.json").open(mode="r") as f:
            data = json.load(f)
            cleaned_data = clean_shodan_result(data)
            shodan_df = pd.DataFrame(cleaned_data)
            print(shodan_df)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Failed to load fallback JSON: {e}")


def clean_shodan_result(shodan_result: dict) -> list:
    cleaned_results = []

    for match in shodan_result.get("matches", []):
        cleaned_result = {
            "ip_str": match.get("ip_str"),
            "city": match.get("location", {}).get("city"),
            "region_code": match.get("location", {}).get("region_code"),
            "longitude": match.get("location", {}).get("longitude"),
            "latitude": match.get("location", {}).get("latitude"),
            "timestamp": match.get("timestamp"),
            "org": match.get("org"),
            "domains": match.get("domains"),
        }
        cleaned_results.append(cleaned_result)

    return cleaned_results


# Example usage
if __name__ == "__main__":
    api = Shodan("YOUR_API_KEY")
    get_data(api)
