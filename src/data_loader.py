import pandas as pd

def load_price_data(filepath):
    """
    Load price data from CSV.
    Returns a pandas DataFrame.
    """
    df = pd.read_csv(filepath)
    return df