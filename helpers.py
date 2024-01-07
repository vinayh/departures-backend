import os
import json
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
    "TFL_APP_KEY": Path(".secrets/tfl_app_key"),
    # 'GOOGLE_CLIENT_ID': Path('.secrets/google_client_id'),
    # 'GOOGLE_CLIENT_SECRET': Path('.secrets/google_client_secret'),
    # 'DATABASE_URL': Path('.secrets/database_url')
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


def stop_to_dict(stop: Stop) -> dict:
    return {"lat": stop.lat, "lon": stop.lon, "id": stop.id, "name": stop.name}


def dep_to_dict(dep: Departure) -> dict:
    return {
        "id": dep.id,
        "line": dep.line,
        "mode": dep.mode,
        "destination": dep.destination,
        "arrival_time": dep.arrival_time.isoformat(),
    }


def dict_to_stop(res_dict: dict) -> Stop:
    return Stop(
        lat=res_dict["lat"],
        lon=res_dict["lon"],
        id=res_dict["id"],
        name=res_dict["commonName"],
        modes=res_dict["modes"],
        distance=res_dict["distance"],
    )


def dict_to_departure(res_dict: dict) -> Departure:
    return Departure(
        id=res_dict["id"],
        line=res_dict["lineId"],
        mode=res_dict["modeName"],
        destination=res_dict["destinationName"]
        if "destinationName" in res_dict
        else "[Unknown]",
        time_to_station=res_dict["timeToStation"],
        arrival_time=datetime.fromisoformat(res_dict["expectedArrival"]),
    )


def departures_for_stop(stop: Stop) -> list[Departure]:
    params = {
        "app_id": TFL_APP_ID,
        "app_key": TFL_APP_KEY,
    }
    res = requests.get(
        ARRIVALS_ENDPOINT.format(stop.id),
        headers={},  # Check about cookie
        params=params,
    )
    res_deps = json.loads(res.text)
    return [dict_to_departure(d) for d in res_deps]
    # return [dict_to_departure(d) for d in res_deps]


def get_departures_for_stops(
    stops_sorted: list[Stop], max_dep_per_stop: int = 5, max_stops: int = 5
) -> list[dict[str, Union[dict, list[dict]]]]:
    departures = []
    for s in stops_sorted:
        if len(departures) > max_stops - 1:
            break
        deps_for_stop_s = sorted(
            departures_for_stop(s), key=lambda d: d.time_to_station
        )
        if len(deps_for_stop_s) > 0:
            departures.append(
                {
                    "station": stop_to_dict(s),
                    "departures": [dep_to_dict(d) for d in deps_for_stop_s[:max_dep_per_stop]],
                }
            )
    return departures


def get_stops(
    lat: float,
    lng: float,
    radius: int = 3000,
    stop_types: str = "NaptanMetroStation",
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
    print("Request params:", params)
    try:
        res = requests.get(
            STOPPOINT_ENDPOINT,
            headers={},  # Check if better to include cookie here?
            params=params,
        )
        res_stops = json.loads(res.text)
        return [dict_to_stop(s) for s in res_stops["stopPoints"]]
    except:
        print(res_stops)
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


def main():
    # Temp hardcoding of variables
    # lat, lng = 51.49454, -0.100601  # E&C
    lat, lng = 51.52009, -0.10508  # Farringdon
    radius = 1200
    stop_types = "NaptanMetroStation,NaptanRailStation"
    # stopTypes = "NaptanMetroStation,NaptanPublicBusCoachTram"
    stops = get_stops(lat, lng, radius=radius, stop_types=stop_types)
    stops_with_departures = get_departures_for_stops(stops)
    # for s in stops_with_departures:
    #     print_departures_for_station(s)


if __name__ == "__main__":
    main()
