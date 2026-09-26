import os

try:
    from app.sources.database_source import extract_database
    from app.sources.csv_source import extract_csv
    from app.sources.api_source import extract_api
except ModuleNotFoundError:
    from sources.database_source import extract_database
    from sources.csv_source import extract_csv
    from sources.api_source import extract_api


def extract_all():
    database_data = extract_database("database/students.db")

    csv_data = extract_csv("data/raw/students.csv")

    api_url = os.getenv("API_URL", "http://127.0.0.1:5000/students")
    api_data = extract_api(api_url)

    return database_data, csv_data, api_data


if __name__ == "__main__":
    database_data, csv_data, api_data = extract_all()

    print(type(api_data))
    print(api_data)

    print(database_data)
    print(csv_data)
