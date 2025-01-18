import sys
from os import environ

from dash import Dash, html
from dotenv import load_dotenv
from shodan import Shodan

from src.utils.get_data import get_data


def main() -> None:
    shodan_clients = initialize_shodan()
    get_data(shodan_clients)
    # launchApp(shodan_clients[0])


class ShodanInitializationError(Exception):
    pass


def initialize_shodan() -> list[Shodan]:
    load_dotenv()
    keys = environ.get("SHODAN_API_KEY")
    if not keys:
        error_msg = "Verify the .env file."
        raise ShodanInitializationError(Exception(error_msg))

    keys = keys.split(",")
    return [Shodan(key) for key in keys]

def launch_app() -> None:
    app = Dash(__name__)
    app.layout = html.Div(children=[html.H1(children="SERVER")])
    app.run_server()


if __name__ == "__main__":
    main()
