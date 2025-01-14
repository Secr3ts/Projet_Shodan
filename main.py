from dotenv import load_dotenv
from shodan import Shodan
from os import environ
from dash import Dash, dcc, html
from layout import layout

def main():
    shodan = initializeShodan()
    launchApp(shodan)

def initializeShodan() -> Shodan:
    load_dotenv()
    
    key = environ.get('SHODAN_API_KEY')
    
    if not key:
        raise Exception("No API key was found. Verify the .env file.")
    
    return Shodan(key)

def launchApp(shodan: Shodan):
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