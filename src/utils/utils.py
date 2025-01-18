"""Utilitary functions for the project."""
from gzip import decompress
from json import JSONDecodeError, loads
from pathlib import Path

from pandas import DataFrame


def setup_directories() -> None:
    """Create required directories and deletes previous data."""
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
    """Decomperss a GZip and returns the path.

    :param path Path: Archive path
    """
    with path.open("rb") as gz:
        compressed = gz.read()
        decompressed = decompress(compressed)
        decompressed_path = path.with_suffix("")
        with decompressed_path.open("wb") as decompressed_file:
            decompressed_file.write(decompressed)
    path.unlink()
    return decompressed_path

def move_geojson_file(file: Path) -> None:
    """Move GeoJSON file to cleaned.

    :param file Path: the GeoJSON file
    """
    file_dest = Path("./", "data", "cleaned", file.parts[-1])
    file.rename(file_dest)


def cleanup_data(directory: Path) -> None:
    """Clean data from a given directory.

    :param directory Path: the directory to clean
    """
    for file in directory.iterdir():
        if file.is_file():
            file.unlink()

def fallback_to_json(callback: callable) -> None:
    """Fallback to the Shodan JSON in case of API Outage for example.

    :param callback callable: callback for data cleaning
    """
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
                data = loads(line)
                cleaned_data.extend(callback(data, fallback=True))
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
    except (JSONDecodeError, FileNotFoundError) as e:
        print(f"Failed to load fallback JSON: {e}")
