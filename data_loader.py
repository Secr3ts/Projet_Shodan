import pandas as pd

def load_csv_data(file_path):
    try:
        data = pd.read_csv(file_path)
        return data
    except FileNotFoundError:
        return pd.DataFrame()

def filter_french_data(df):
    return df[df['Country'] == 'France']