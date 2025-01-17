from os import environ

from dash import Dash
from dotenv import load_dotenv
from shodan import Shodan

from callback import register_callbacks
from get_data import get_data
from layout import create_layout


def main() -> None:
    shodan_clients = initialize_shodan()
    get_data(shodan_clients)

def initialize_shodan() -> list[Shodan]:
    load_dotenv()

    keys = environ.get("SHODAN_API_KEY")
    print(keys)
    if not keys:
        raise Exception("No API key was found. Verify the .env file.")

    keys = keys.split(",")
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
