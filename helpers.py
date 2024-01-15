import os
import json
import asyncio
import aiohttp
import logging
import requests

from dataclasses import dataclass
from dataclasses_json import dataclass_json
from pathlib import Path

STOPPOINT_ENDPOINT = "https://api.tfl.gov.uk/StopPoint"
ARRIVALS_ENDPOINT = "https://api.tfl.gov.uk/StopPoint/{}/Arrivals"

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

@dataclass_json
@dataclass
class Stop:
    id: str
    lat: float
    lon: float
    name: str
    modes: str
    distance: float

    def __init__(self, res_dict: dict):
        self.lat = res_dict["lat"]
        self.lon = res_dict["lon"]
        self.id = res_dict["id"]
        self.name = res_dict["commonName"]
        self.modes = res_dict["modes"]
        self.distance = res_dict["distance"]

    async def departures(self, max_departures: int = 12):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                ARRIVALS_ENDPOINT.format(self.id),
                headers={},  # Check about cookie
                params=API_PARAMS,
            ) as res:
                print("Status", res.status)
                data = await res.json()
                return sorted(
                    [Departure(d) for d in data[:max_departures]],
                    key=lambda x: x.time_to_station,
                )

@dataclass_json
@dataclass
class Departure:
    id: str
    line: str
    mode: str
    destination: str
    arrival_time: str

    def __init__(self, res_dict: dict):
        self.id = res_dict["id"]
        self.line = res_dict["lineId"]
        self.mode = res_dict["modeName"]
        self.destination = res_dict["destinationName"] if "destinationName" in res_dict else "[Unknown]"
        self.time_to_station = res_dict["timeToStation"]
        self.arrival_time = res_dict["expectedArrival"]

@dataclass_json
@dataclass
class StationDepartures:
    station: Stop
    departures: list[Departure]


def departures_for_all_stops(
    stops_sorted: list[Stop], max_dep_per_stop: int = 12, max_stops: int = 6
) -> list[StationDepartures]:
    async def helper():
        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(s.departures(max_dep_per_stop)) for s in stops_sorted[:max_stops]]
        return [t.result() for t in tasks]

    results: list[list[Departure]] = asyncio.run(helper())
    return [StationDepartures(station=stops_sorted[i], departures=results[i]) for i in range(len(results)) if len(results[i]) > 0]


def nearest_stops(
    lat: str,
    lng: str,
    radius: int = 3000,
    stop_types: str = "NaptanMetroStation,NaptanRailStation",
    modes: str = "tube,dlr,overground,bus",
    categories: str = "none",
) -> list[Stop]:
    
    params = {
        # "useStopPointHierarchy": "true",
        "lat": lat,
        "lon": lng,
        "radius": radius,
        "stopTypes": stop_types,
        "categories": categories,
        "modes": modes,
    }
    params.update(API_PARAMS)

    try:
        res = requests.get(
            STOPPOINT_ENDPOINT,
            headers={},  # TODO: Check if better to include cookie here?
            params=params,
        )
        res_stops = json.loads(res.text)
        return [Stop(s) for s in res_stops["stopPoints"]]
    except Exception as e:
        logging.error(e)
        raise


# TODO: Not yet fully updated to work with stop/dest dicts
# def print_departures_for_station(stop_with_deps: dict[str, Union[dict, list[dict]]]) -> None:

#     print(stop_with_deps['station'].keys())
#     # print(f"{stop_with_deps['station']['name']} - {stop_with_deps['station']['distance']:.0f}m away")
#     print(stop_with_deps['station']['name'])
#     print(
#         "\n".join(
#             [
#                 f"\t{d['arrival_time'] // 60}min - {d['destination']}"
#                 for d in stop_with_deps["departures"]
#             ]
#         ),
#     )


def nearest_departures_json(
    lat, lng, stop_types="NaptanMetroStation,NaptanRailStation"
) -> str:
    stop_types = (
        stop_types if stop_types is not None else "NaptanMetroStation,NaptanRailStation"
    )
    stops = nearest_stops(lat, lng, radius=2000, stop_types=stop_types)
    return StationDepartures.schema().dumps(departures_for_all_stops(stops), many=True)
