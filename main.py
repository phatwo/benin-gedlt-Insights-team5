from src.extract import extract_data
from src.transform import transform_data
from src.load import load_data


def main():
    df = extract_data()

    df_clean = transform_data(df)

    load_data(df_clean)

    print("Pipeline ETL terminé avec succès")


if __name__ == "__main__":
    main()