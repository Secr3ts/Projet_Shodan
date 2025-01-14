import sys
from os import environ

from dash import Dash, html
from dotenv import load_dotenv
from shodan import Shodan

from get_data import get_data

from os import environ
from dash import Dash, dcc, html
from layout import layout

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
    external_script = [
        "https://cdn.tailwindcss.com"
    ]
    
    app = Dash(
        __name__,
        external_scripts=external_script,
    )
    app.scripts.config.serve_locally = True
    
    app.layout = layout
    
    app.run_server(debug=True)


if __name__ == "__main__":
    main()
