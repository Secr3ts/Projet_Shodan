"""Main file."""
from os import environ

from dash import Dash
from dotenv import load_dotenv
from shodan import Shodan

from callback import register_callbacks
from layout import create_layout
from src.utils.get_data import get_data


def main() -> None:
    """Point d'entrée principal de l'application."""
    shodan_clients = initialize_shodan()
    get_data(shodan_clients)
    launch_app()


class ShodanInitializationError(Exception):
    """Dummy class for errors."""


def initialize_shodan() -> list[Shodan]:
    """Initialise les clients Shodan."""
    load_dotenv()
    raw_keys = environ.get("SHODAN_API_KEY")
    if not raw_keys:
        error_msg = "Verify the .env file."
        raise ShodanInitializationError(Exception(error_msg))

    keys = raw_keys.split(",")
    return [Shodan(key) for key in keys]


def launch_app() -> None:
    """Lance l'application Dash avec le layout personnalisé."""
    external_scripts = [
        "https://cdn.tailwindcss.com",
    ]

    app = Dash(
        __name__,
        external_scripts=external_scripts,
    )
    app.scripts.config.serve_locally = True

    app.layout = create_layout()

    register_callbacks(app)

    app.run_server(debug=True)


if __name__ == "__main__":
    main()
