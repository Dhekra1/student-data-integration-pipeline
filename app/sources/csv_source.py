import pandas as pd
from pathlib import Path


def extract_csv(path):
    csv_path = Path(path)

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    df = pd.read_csv(csv_path)

    return df


if __name__ == "__main__":
    data = extract_csv("data/raw/students.csv")

    print(type(data))
    print(data)