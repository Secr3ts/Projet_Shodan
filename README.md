This project serves as a proof-of-concept of correlating crime rates with the number of cameras throughout France. Specifically aimed at 2016-2023 due to a lack of data before and after this period.

### Table of Contents

- [User Guide](#user-guide)
    - [Downloading](#downloading)
    - [Installing](#installing)
    - [Running](#running)
- [Data](#data)
    - [Sources](#sources)
    - [Usage](#usage)
- [Developer Guide](#developer-guide)
    - [Main files](#main-files)
- [Analysis Report](#analysis-report)
- [License](#license)

## User Guide

### Downloading
Simply `git clone` this repository.
Sample command below:

```sh
git clone https://github.com/Secr3ts/Projet_Shodan
```

### Installing
This project works with `Python 3.11.x`.
For maximum compatibility, please use [`Python 3.11`](https://www.python.org/downloads/release/python-3119/).

### Running
To run the dashboard, cd into the Projet_Shodan directory and type `python main.py`. Then visit [this](http://localhost:8050) page.

## Data

### Sources
The data used in this project comes from:
- [INSEE](https://insee.fr) (French cities outline)
- [GOUV.fr](https://data.gouv.fr) (crime rates ranging from 2016 to 2023)
- [Shodan](https://shodan.io) (publicly available cameras)
- [Overpass Turbo](https://overpass-turbo.eu/) (secondary source for publicly available cameras)

### Usage
Les données sont utilisées de la manière suivante :

- **INSEE** : The boundaries of French municipalities are used to create the base choropleth map. Each municipality is represented by a polygon with its geographical coordinates.

- **GOUV.fr** : Crime rates are cleaned and normalized to be displayed on the map. The data is aggregated by municipality and year, enabling a temporal visualization of crime trends.

- **Shodan** : Camera data is geolocated and filtered to include only public cameras in France. These points are overlaid on the map of municipalities.

- **Overpass Turbo** : A complementary source for surveillance cameras, used to validate and enrich Shodan data.


## Developer Guide
The code is structured in two main parts:
- A backend that fetches data, cleans it, and stores it
- A frontend that makes use of this data and displays it accordingly for the user to view.

Putting it simply, the program first calls `get_data` located in `get_data.py` to fetch all the data, then `get_data` calls the cleansing functions of each data retrieved and moves them to the cleaned folder.

## Dashboard Functionality
The dashboard is built around two main concepts: Layout and Callbacks.

### Layout
The layout defines the visual structure of the dashboard using a component-based approach:
- The page is divided into sections using a modern CSS grid.
- Each chart (map, histograms, etc.) is encapsulated in a dcc.Graph component.
- User controls (sliders, dropdowns) are integrated to enable interactivity.
- User controls (sliders, dropdowns) are integrated to enable interactivity.

### Callbacks
Callbacks handle the interactivity of the dashboard:
- Callbacks handle the interactivity of the dashboard:
- Example: When a user selects a year, the callbacks update:
  - The map with crime data for the selected year.
  - The map with crime data for the selected year.
  - The map with crime data for the selected year.
- Data is dynamically filtered and transformed based on the selections.

Below is a diagram that explains the relations between different files of our codebase.
```mermaid
graph TD
    A[main.py] -->|calls| B[initialize_shodan]
    A -->|calls| C[launch_app]
    A -->|calls| D[get_data]
    B -->|loads| E[.env]
    D -->|calls| F[setup_directories]
    D -->|calls| G[clean_csv_data]
    D -->|calls| H[clean_osm_data]
    D -->|calls| I[clean_shodan_result]
    D -->|calls| J[download_data]
    D -->|calls| K[decompress_gz]
    D -->|calls| L[move_geojson_file]
    D -->|calls| M[cleanup_data]
    D -->|calls| N[fallback_to_json]
    C -->|uses| O[Dash]
    C -->|uses| P[html]
    C -->|uses| Q[dcc]
    C -->|calls| R[create_layout]
    C -->|calls| S[register_callbacks]
    subgraph utils
        F[setup_directories]
        G[clean_csv_data]
        H[clean_osm_data]
        I[clean_shodan_result]
        J[download_data]
        K[decompress_gz]
        L[move_geojson_file]
        M[cleanup_data]
        N[fallback_to_json]
    end
    subgraph components
        S[register_callbacks]
        R[create_layout]
    end
```

## Analysis Report

With the extracted data, our dashboard led to the following conclusions:

- Each year, the crime rate is on the rise.
- This implicitly leads to an increase in security camera installations (cf. causality).

The crime rates dataset specifically showed that the closer to a big city, the higher the risk which is a proven fact.

However, everything needs to be taken with a grain of salt, as the data we have selected has been proven to be incomplete. For example, the crime dataset has data that is not disclosed (see [this](./lienverslemetadata/))

## Copyright

We certify and swear on our honor that each line of code that has been borrowed is credited to its rightful owner and everything else is solely ours. All resemblance with an existing project/file is purely coincidental.
=======
# Projet Camera/Crimes
