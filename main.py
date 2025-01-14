import sys
from os import environ

from dash import Dash, html
from dotenv import load_dotenv
from shodan import Shodan

from get_data import get_data


def main() -> None:
    shodan_clients = initialize_shodan()
    get_data(shodan_clients)
    # launchApp(shodan_clients[0])


def initialize_shodan() -> list[Shodan]:
    load_dotenv()

    keys = environ.get("SHODAN_API_KEY")
    print(keys)
    if not keys:
        raise Exception("No API key was found. Verify the .env file.")

    keys = keys.split(",")
    return [Shodan(key) for key in keys]

def launch_app(shodan: Shodan):
    app = Dash(__name__)
    app.layout = html.Div(children=[html.H1(children="SERVER")])
    app.run_server()


if __name__ == "__main__":
    main()
