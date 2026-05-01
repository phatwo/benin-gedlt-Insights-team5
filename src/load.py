def load_data(df):

    df.to_csv(
        "data/processed/gdelt_benin_clean.csv",
        index=False
    )

    df.to_parquet(
        "data/processed/gdelt_benin_clean.parquet",
        index=False
    )

    print("Chargement terminé")