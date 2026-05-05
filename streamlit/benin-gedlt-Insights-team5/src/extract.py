import pandas as pd

def extract_data(path="data/raw/gdelt_benin_2025.csv"):
    df = pd.read_csv(path)
    print(f" Données chargées : {df.shape}")
    return df

