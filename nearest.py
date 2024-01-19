import json
import asyncio
import aiohttp
import logging
import requests

from typing import Optional
from haversine import haversine, Unit
from dataclasses import dataclass
from dataclasses_json import dataclass_json

from helpers import (
    API_PARAMS,
    read_pickle_all_stops,
    pickle_metro_rail_stops,
    load_cached_stops,
    CachedStop,
)

STOPPOINT_ENDPOINT = "https://api.tfl.gov.uk/StopPoint"
ARRIVALS_ENDPOINT = "https://api.tfl.gov.uk/StopPoint/{}/Arrivals"


@dataclass_json
@dataclass
class Stop:
    id: str
    lat: float
    lon: float
    name: str
    stop_type: str
    modes: list[str]
    distance: float

    async def departures(self, modes_set, max_departures):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                ARRIVALS_ENDPOINT.format(self.id),
                headers={},  # Check about cookie
                params=API_PARAMS,
            ) as res:
                print("Status", res.status)
                data = await res.json()
                sorted_departures = sorted(
                    [Departure(d) for d in data], key=lambda x: x.time_to_station
                )
                return [d for d in sorted_departures if d.mode in modes_set][:max_departures]

    @staticmethod
    def init_from_cached(cached: CachedStop, distance: float):
        return Stop(
            id=cached.id,
            lat=cached.lat,
            lon=cached.lon,
            name=cached.name,
            stop_type=cached.stop_type,
            modes=cached.modes,
            distance=distance,
        )

    @staticmethod
    def init_from_dict(res_dict: dict) -> "Stop":
        print(res_dict["commonName"])
        return Stop(
            id=res_dict["id"],
            lat=res_dict["lat"],
            lon=res_dict["lon"],
            name=res_dict["commonName"],
            stop_type=res_dict["stopType"],
            modes=res_dict["modes"],
            distance=res_dict["distance"],
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
        self.destination = (
            res_dict["destinationName"]
            if "destinationName" in res_dict
            else "[Unknown]"
        )
        self.time_to_station = res_dict["timeToStation"]
        self.arrival_time = res_dict["expectedArrival"]


@dataclass_json
@dataclass
class StationDepartures:
    station: Stop
    departures: list[Departure]


@dataclass_json
@dataclass
class Response:
    stnsDeps: list[StationDepartures]
    lat: float
    lng: float


def departures_for_all_stops(
    stops_sorted: list[Stop], modes: str, max_dep_per_stop: int = 25, max_stops: int = 6
) -> list[StationDepartures]:
    modes_set = set([m for m in modes.split(",") if len(m) > 0])

    async def helper():
        async with asyncio.TaskGroup() as tg:
            tasks = [
                tg.create_task(s.departures(modes_set, max_dep_per_stop))
                for s in stops_sorted[:max_stops]
            ]
        return [t.result() for t in tasks]

    results: list[list[Departure]] = asyncio.run(helper())
    return [
        StationDepartures(station=stops_sorted[i], departures=results[i])
        for i in range(len(results))
        if len(results[i]) > 0
    ]


def nearest_stops_request(
    lat: str,
    lng: str,
    stop_types: str = "NaptanMetroStation,NaptanRailStation",
    num_stops: int = 15,
    radius: int = 3000,
) -> list[Stop]:
    params = {
        # "useStopPointHierarchy": "true",
        "lat": lat,
        "lon": lng,
        "radius": radius,
        "stopTypes": stop_types,
        "categories": "none",
        # "modes": modes,
    }
    params.update(API_PARAMS)

    try:
        res = requests.get(
            STOPPOINT_ENDPOINT,
            headers={},  # TODO: Check if better to include cookie here?
            params=params,
        )
        res_stops = json.loads(res.text)
        return [Stop.init_from_dict(s) for s in res_stops["stopPoints"][:num_stops]]
    except Exception as e:
        logging.error(e)
        raise


def nearest_stops_cached(
    lat: str,
    lng: str,
    stop_types: str,
    num_stops: int = 10,
    radius: int = 3000,
) -> list[Stop]:
    stop_types_list = [s for s in stop_types.split(",") if len(s) > 0]
    dist_to_stop = lambda s: haversine(
        (float(lat), float(lng)), (s.lat, s.lon), unit=Unit.METERS
    )
    cached_stops = load_cached_stops(stop_types_list)
    cached_stops_by_dist = sorted(cached_stops, key=dist_to_stop)
    top_n_stops = [
        Stop.init_from_cached(c, distance=dist_to_stop(c))
        for c in cached_stops_by_dist[:num_stops]
    ]
    return [s for s in top_n_stops if s.distance < radius]


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
    lat: str,
    lng: str,
    stop_types: Optional[str],
    modes: Optional[str],
) -> str:
    stop_types = (
        "NaptanMetroStation,NaptanRailStation" if stop_types is None else stop_types
    )
    modes = "tube,dlr,overground,elizabeth-line,bus" if modes is None else modes

    stops = nearest_stops_cached(lat, lng, radius=2000, stop_types=stop_types)
    stnsDeps = departures_for_all_stops(stops, modes)

    return Response.schema().dumps(Response(stnsDeps=stnsDeps, lat=lat, lng=lng))


if __name__ == "__main__":
    filenames = [
        "data/all_stops_2024-01-18_page_1.json",
        "data/all_stops_2024-01-18_page_2.json",
        "data/all_stops_2024-01-18_page_3.json",
    ]
    all_stops = read_pickle_all_stops(filenames)
    metro_rail_stops = pickle_metro_rail_stops(all_stops)
