import os
import json
import asyncio
import aiohttp
import logging
import requests

from collections import namedtuple
from datetime import datetime
from pathlib import Path
from typing import Union

STOPPOINT_ENDPOINT = "https://api.tfl.gov.uk/StopPoint"
ARRIVALS_ENDPOINT = "https://api.tfl.gov.uk/StopPoint/{}/Arrivals"

SECRETS_TO_PATHS = {
    "FLASK_SECRET_KEY": Path(".secrets/flask_secret_key"),
    "TFL_APP_ID": Path(".secrets/tfl_app_id"),
    "TFL_APP_KEY": Path(".secrets/tfl_app_key")
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


TFL_APP_ID = get_secret("TFL_APP_ID")
TFL_APP_KEY = get_secret("TFL_APP_KEY")


Stop = namedtuple("Stop", ["lat", "lon", "id", "name", "modes", "distance"])

Departure = namedtuple(
    "Departure",
    ["id", "line", "mode", "destination", "time_to_station", "arrival_time"],
)


def dict_to_stop(res_dict: dict) -> Stop:    return Stop(
        lat=res_dict["lat"],
        lon=res_dict["lon"],
        id=res_dict["id"],
        name=res_dict["commonName"],
        modes=res_dict["modes"],
        distance=res_dict["distance"],
    )


# def dict_to_departure(res_dict: dict) -> Departure:
#     return Departure(
#         id=res_dict["id"],
#         line=res_dict["lineId"],
#         mode=res_dict["modeName"],
#         destination=res_dict["destinationName"]
#         if "destinationName" in res_dict
#         else "[Unknown]",
#         time_to_station=res_dict["timeToStation"],
#         arrival_time=res_dict["expectedArrival"],
#     )

def format_departure_response(res_dict: dict) -> dict:
    return {
        "id": res_dict["id"],
        "line": res_dict["lineId"],
        "mode": res_dict["modeName"],
        "destination": res_dict["destinationName"]
        if "destinationName" in res_dict
        else "[Unknown]",
        "time_to_station": res_dict["timeToStation"],
        "arrival_time": res_dict["expectedArrival"],
    }


async def departures_for_stop(stop: Stop, max_dep_per_stop: int) -> list[dict]:
    params = {
        "app_id": TFL_APP_ID,
        "app_key": TFL_APP_KEY,
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(
            ARRIVALS_ENDPOINT.format(stop.id),
            headers={},  # Check about cookie
            params=params,
        ) as res:
            print('Status', res.status)
            data = await res.json()
            return sorted([format_departure_response(d) for d in data[:max_dep_per_stop]], key=lambda x: x["time_to_station"])


def get_departures_for_stops(
    stops_sorted: list[Stop], max_dep_per_stop: int = 5, max_stops: int = 6
) -> list[dict[str, Union[dict, list[dict]]]]:
    stops = stops_sorted[:max_stops]
    async def async_get_departures():
        coroutines = [departures_for_stop(s, max_dep_per_stop) for s in stops]
        return await asyncio.gather(*coroutines)
    
    results: list[list[dict]] = asyncio.run(async_get_departures())
    return [{"station": stops_sorted[i]._asdict(), "departures": results[i]} for i in range(len(stops))]


def get_stops(
    lat: str,
    lng: str,
    radius: int = 3000,
    stop_types: str = "NaptanMetroStation,NaptanRailStation",
    categories: str = "none",
) -> list[Stop]:
    params = {
        "app_id": TFL_APP_ID,
        "app_key": TFL_APP_KEY,
        # "useStopPointHierarchy": "true",
        "lat": lat,
        "lon": lng,
        "radius": radius,
        "stopTypes": stop_types,
        "categories": categories,
    }
    res_stops = None
    try:
        res = requests.get(
            STOPPOINT_ENDPOINT,
            headers={},  # TODO: Check if better to include cookie here?
            params=params,
        )
        res_stops = json.loads(res.text)
        print(res_stops)
        return [dict_to_stop(s) for s in res_stops["stopPoints"]]
    except:
        logging.error(res_stops)
        raise


def print_departures_for_station(stop_with_deps: dict[str, Union[dict, list[dict]]]) -> None:
    # TODO: Not yet fully updated to work with stop/dest dicts
    print(stop_with_deps['station'].keys())
    # print(f"{stop_with_deps['station']['name']} - {stop_with_deps['station']['distance']:.0f}m away")
    print(stop_with_deps['station']['name'])
    print(
        "\n".join(
            [
                f"\t{d['arrival_time'] // 60}min - {d['destination']}" 
                for d in stop_with_deps["departures"]
            ]
        ),
    )
