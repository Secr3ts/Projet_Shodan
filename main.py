import sys
from os import environ

from dash import Dash, html
from dotenv import load_dotenv
from shodan import Shodan

from get_data import get_data


def main() -> None:
    shodan = initialize_shodan()
    get_data(shodan)
    # launchApp(shodan)


def initialize_shodan() -> Shodan:
    load_dotenv()

    keys = environ.get("SHODAN_API_KEY")
    print(keys)
    if not keys:
        msg = "No API key was found. Verify the .env file."
        raise Exception(msg)
    valid_keys = []
    for key in keys:
        if Shodan(key).info()["usage_limits"]["query_credits"] < 1:
            break
        valid_keys.append(key)
    return 


def launch_app(shodan: Shodan):
    app = Dash(__name__)
    app.layout = html.Div(children=[html.H1(children="SERVER")])
    app.run_server()


if __name__ == "__main__":
    main()
