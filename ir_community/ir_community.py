import json
from pyalex import Works
import os
from tqdm import tqdm
import requests
import pandas as pd


def load_ror_dump(path="data/raw/ror/v1.25-2023-05-11-ror-data.json"):
    with open(path) as file:
        ror_raw = json.load(file)
    ror = {}
    for institute in ror_raw:
        ror[institute["id"]] = institute
    return ror


# Enrichment
# Open Alex
def get_open_alex_work_by_doi(doi):
    open_alex_metadata = Works()["https://doi.org/" + doi]
    return open_alex_metadata


def enriche_with_open_alex(conference):
    # create cace if not exists
    if os.path.exists(f"data/interim/dblp_{conference}_openalex.jsonl"):
        with open(f"data/interim/dblp_{conference}_openalex.jsonl", "r") as f:
            publications_alex = [json.loads(line) for line in f.readlines()]
    else:
        # create empty file
        open(f"data/interim/dblp_{conference}_openalex.jsonl", "w").close()
        with open(f"data/interim/dblp_{conference}_openalex.jsonl", "r") as f:
            publications_alex = [json.loads(line) for line in f.readlines()]

    # loade publications
    with open(f"data/raw/dblp_{conference}.jsonl", "r") as f:
        publications = [json.loads(line) for line in f.readlines()]

    # enrich all publications
    for publication in tqdm(publications):
        if publication in publications_alex:
            continue
        if publication["info"].get("doi"):
            try:
                metadata = get_open_alex_work_by_doi(publication["info"].get("doi"))
                publication["openalex"] = metadata
                with open(f"data/interim/dblp_{conference}_openalex.jsonl", "a") as f:
                    f.write(json.dumps(publication) + "\n")
            except requests.HTTPError as e:
                print("doi not found")
                with open(
                    f"data/interim/dblp_{conference}_openalex_errors.jsonl", "a"
                ) as f:
                    f.write(json.dumps(publication) + "\n")
                with open(f"data/interim/dblp_{conference}_openalex.jsonl", "a") as f:
                    publication["openalex"] = None
                    f.write(json.dumps(publication) + "\n")
        else:
            publication["openalex"] = None
            with open(f"data/interim/dblp_{conference}_openalex.jsonl", "a") as f:
                f.write(json.dumps(publication) + "\n")


# ROR
class ROR:
    def __init__(self):
        self.ror = load_ror_dump()

    def get_ror_by_id(self, ror_id):
        return self.ror.get(ror_id)


def enriche_with_ror(conference):
    # load ror data
    ror = ROR()

    # loade publications
    with open(f"data/interim/dblp_{conference}_openalex.jsonl", "r") as f:
        publications = [json.loads(line) for line in f.readlines()]

    # enrich all publications
    def enrich_authors_institutions_ror(author):
        enriched_institutions = []
        for institution in author["institutions"]:
            ror_data = ror.get_ror_by_id(institution["ror"])
            institution["ror_data"] = ror_data
            enriched_institutions.append(institution)
        author["institutions"] = enriched_institutions
        return author

    def enrich_authors_ror(publication):
        if not publication.get("openalex"):
            return publication
        enriched_authors = [
            enrich_authors_institutions_ror(author)
            for author in publication["openalex"]["authorships"]
        ]
        publication["openalex"]["authorships"] = enriched_authors
        return publication

    # apply
    publications = [enrich_authors_ror(publication) for publication in publications]

    # save
    with open(f"data/interim/dblp_{conference}_openalex_ror.jsonl", "w") as f:
        for publication in publications:
            f.write(json.dumps(publication) + "\n")


# Gerid
class Gerit:
    def __init__(self):
        self.gerid = self.load_gerid_dump()

    def load_gerid_dump(self):
        df = pd.read_excel("data/raw/institutionen_gerit.xlsx")
        df.dropna(subset=["ROR ID"], inplace=True)
        df.drop_duplicates(subset=["ROR ID"], inplace=True)
        df.set_index("ROR ID", inplace=True)
        gerit = df.to_dict(orient="index")
        return gerit

    def get_gerid_by_id(self, gerid_id):
        return self.gerid.get(gerid_id)


def enriche_with_gerit(conference):
    # load gerid dump
    gerit = Gerit()

    # loade publications
    with open(f"data/interim/dblp_{conference}_openalex_ror.jsonl", "r") as f:
        publications = [json.loads(line) for line in f.readlines()]

    def enrich_authors_institutions_gerit(author):
        enriched_institutions = []
        for institution in author["institutions"]:
            gerit_data = gerit.get_gerid_by_id(institution["ror"])
            institution["gerit_data"] = gerit_data
            enriched_institutions.append(institution)
        author["institutions"] = enriched_institutions
        return author

    def enrich_authors_gerit(publication):
        if not publication.get("openalex"):
            return publication
        enriched_authors = [
            enrich_authors_institutions_gerit(author)
            for author in publication["openalex"]["authorships"]
        ]
        publication["openalex"]["authorships"] = enriched_authors
        return publication

    publications = [enrich_authors_gerit(publication) for publication in publications]

    # save
    with open(f"data/interim/dblp_{conference}_openalex_ror_gerit.jsonl", "w") as f:
        for publication in publications:
            f.write(json.dumps(publication) + "\n")
