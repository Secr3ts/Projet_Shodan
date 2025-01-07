from dotenv import load_dotenv
from shodan import Shodan
from os import environ
from dash import Dash, dcc, html
from get_data import get_data

def main():
    shodan = initializeShodan()
    get_data(shodan)
    # launchApp(shodan)


def initializeShodan() -> Shodan:
    load_dotenv()
    
    key = environ.get('SHODAN_API_KEY')
    
    if not key:
        raise Exception("No API key was found. Verify the .env file.")
    
    return Shodan(key)

def launchApp(shodan: Shodan):
    app = Dash(__name__)
    #
    app.layout = html.Div(
        children=[
            html.H1(children="SERVER")
        ]
    )
    app.run_server()

if __name__ == "__main__":
    main()