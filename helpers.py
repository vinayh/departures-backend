import os
import json
import pickle
import requests

from pathlib import Path

SECRETS_TO_PATHS = {
    "FLASK_SECRET_KEY": Path(".secrets/flask_secret_key"),
    "TFL_APP_ID": Path(".secrets/tfl_app_id"),
    "TFL_APP_KEY": Path(".secrets/tfl_app_key"),
}


def get_secret(name: str) -> str:
    env_name = os.getenv("DEPARTURES_ENV")
    if env_name == "RENDER":
        return get_secret_from_file(SECRETS_TO_PATHS[name].relative_to(".secrets"))
    elif env_name == "FLY" or env_name == "AZURE_FUNCTION":
        if name in os.environ:
            return os.getenv(name)
        else:
            raise Exception
    else:
        return get_secret_from_file(SECRETS_TO_PATHS[name])


def get_secret_from_file(path) -> str:
    try:
        with path.open("r") as f:
            return f.read()
    except:
        print(f"Error getting secret {path}")
        raise

API_PARAMS = {
    "app_id": get_secret("TFL_APP_ID"),
    "app_key": get_secret("TFL_APP_KEY"),
}

STOPPOINT_MODE_ENDPOINT = "https://api.tfl.gov.uk/StopPoint/Mode"
STOPPOINT_MODES = "dlr,elizabeth-line,overground,tram,tube"
CACHED_STOPS_PATH = "data/metro_rail_stops.pkl"

class CachedLine:
    id: str
    name: str

    def __init__(self, res_dict: dict):
        self.id = res_dict["id"]
        self.name = res_dict["name"]


class CachedStop:
    id: str
    lat: float
    lon: float
    name: str
    stop_type: str
    naptan_id: str
    modes: list[str]
    lines: list[CachedLine]

    def __init__(self, res_dict: dict):
        self.id = res_dict["id"]
        self.lat = res_dict["lat"]
        self.lon = res_dict["lon"]
        self.name = res_dict["commonName"]
        self.stop_type = res_dict["stopType"]
        self.naptan_id = res_dict["naptanId"]
        self.modes = res_dict["modes"]
        self.lines = [CachedLine(line) for line in res_dict["lines"]]


def download_all_stops():
    endpoint = f"{STOPPOINT_MODE_ENDPOINT}/{STOPPOINT_MODES}"
    try:
        res = requests.get(
            endpoint,
            headers={},  # TODO: Check if better to include cookie here?
            params=API_PARAMS,
        )
        print(f"Got response, status {res.status_code}")
        if not res.ok:
            raise Exception(f"Response status {res.status_code}")
        with open("all_stops_2024-01-18.json", mode="wt") as f:
            f.write(res.text)
    except Exception as e:
        print.error(e)
        raise
    print("Saved JSON response to file")


def read_pickle_all_stops(filenames: list[str]) -> list[CachedStop]:
    all_stops = []
    for file in filenames:
        try:
            with open(file, mode="rt") as f:
                stops_json = f.read()
            print(f"Read JSON from file {file}")
            res_stops = json.loads(stops_json)
            all_stops += [CachedStop(s) for s in res_stops["stopPoints"]]
        except Exception as e:
            print.error(e)
            raise
    with open("all_stops.pkl", mode="wb") as f:
        pickle.dump(all_stops, f)
        print("Saved all stops pickle to file")
        return all_stops


def pickle_metro_rail_stops(all_stops: list[CachedStop]) -> list[CachedStop]:
    metro_rail_stops = [
        x
        for x in all_stops
        if x.stop_type == "NaptanMetroStation" or x.stop_type == "NaptanRailStation"
    ]
    with open(CACHED_STOPS_PATH, mode="wb") as f:
        pickle.dump(metro_rail_stops, f)
        print("Saved metro/rail stops pickle to file")
        return metro_rail_stops

def load_cached_stops(stop_types_list: list[str]) -> list[CachedStop]:
    with open(CACHED_STOPS_PATH, mode="rb") as f:
        cached_stops = pickle.load(f)
    return [c for c in cached_stops if c.stop_type in stop_types_list]

if __name__ == "__main__":
    # download_all_stops()
    filenames = [
        "data/all_stops_2024-01-18_page_1.json",
        "data/all_stops_2024-01-18_page_2.json",
        "data/all_stops_2024-01-18_page_3.json",
    ]
    all_stops = read_pickle_all_stops(filenames)
    metro_rail_stops = pickle_metro_rail_stops(all_stops)
