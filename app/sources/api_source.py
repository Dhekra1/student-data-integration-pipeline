import requests


def extract_api(url):
    response = requests.get(url)

    response.raise_for_status()

    data = response.json()

    return data