"""Main file."""
from os import environ

from dash import Dash
from dotenv import load_dotenv
from shodan import Shodan

from callback import register_callbacks
from get_data import get_data
from layout import create_layout
from src.utils.get_data import get_data


def main() -> None:
    shodan_clients = initialize_shodan()
    get_data(shodan_clients)


class ShodanInitializationError(Exception):
    """Dummy class for errors."""


def initialize_shodan() -> list[Shodan]:
    load_dotenv()
    raw_keys = environ.get("SHODAN_API_KEY")
    if not raw_keys:
        error_msg = "Verify the .env file."
        raise ShodanInitializationError(Exception(error_msg))

    keys = raw_keys.split(",")
    return [Shodan(key) for key in keys]

def create_app():
    external_script = [
        "https://cdn.tailwindcss.com",
    ]

    app = Dash(
        __name__,
        external_scripts=external_script,
    )
    app.scripts.config.serve_locally = True

    app.layout = create_layout()

    register_callbacks(app)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run_server(debug=True)
