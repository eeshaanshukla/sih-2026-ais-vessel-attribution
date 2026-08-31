import pandas as pd


def load_ais(path):
    """Load AIS observations from a CSV file."""
    df = pd.read_csv(path)

    # Convert timestamp strings into timezone-aware datetime values.
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

    return df


if __name__ == "__main__":
    ais = load_ais("data/synthetic_ais.csv")

    print("AIS records:", len(ais))
    print("Vessels:", ais["vessel_id"].nunique())
    print()
    print(ais.head())