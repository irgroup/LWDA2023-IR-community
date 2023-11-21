import json


def load_ror_dump(path="data/raw/ror/v1.25-2023-05-11-ror-data.json"):
    with open(path) as file:
        ror_raw = json.load(file)
    ror = {}
    for institute in ror_raw:
        ror[institute["id"]] = institute
    return ror
