import pandas as pd

def transform_data(df):
    rename_columns = {
        "SQLDATE": "date",
        "Year": "year",
        "MonthYear": "month_year",
        "Actor1Name": "actor1_name",
        "Actor1Type1Code": "actor1_type",
        "Actor2Name": "actor2_name",
        "Actor2Type1Code": "actor2_type",
        "EventCode": "event_code",
        "EventBaseCode": "event_base_code",
        "EventRootCode": "event_root_code",
        "QuadClass": "quad_class",
        "GoldsteinScale": "goldstein_scale",
        "NumMentions": "num_mentions",
        "NumSources": "num_sources",
        "NumArticles": "num_articles",
        "AvgTone": "avg_tone",
        "ActionGeo_Type": "geo_type",
        "ActionGeo_FullName": "location_name",
        "ActionGeo_CountryCode": "country_code",
        "ActionGeo_ADM1Code": "admin_code",
        "ActionGeo_Lat": "latitude",
        "ActionGeo_Long": "longitude",
        "SOURCEURL": "source_url"
    }

    # On travaille sur une copie pour éviter les SettingWithCopyWarning
    df = df.rename(columns=rename_columns).copy()

    # Conversion date int en datetime (format YYYYMMDD)
    df["date"] = pd.to_datetime(
        df["date"].astype(str),
        format="%Y%m%d",
        errors="coerce"
    )

    # Ajouter colonne mois (extrait le mois depuis la date)
    df["month_name"] = df["date"].dt.month_name()

    # Supprimer colonne inutile
    df.drop(columns=["month_year"], inplace=True)

    # Valeurs manquantes remplacées par "Unknown" 
    cols = ["actor1_name", "actor1_type", "actor2_name", "actor2_type"]
    df[cols] = df[cols].fillna("Unknown")

    # Suppression des doublons
    df = df.drop_duplicates()

    print("Nettoyage terminée")

    return df