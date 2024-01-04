from json import dumps
from flask import Flask, Response, request
from werkzeug.exceptions import abort

from helpers import get_stops, get_departures_for_stops

app = Flask(__name__)


@app.route("/nearest")
def nearest():
    """
    - Check cache - TODO
    - If not in cache, get stops within radius from TfL API - DONE
    - Return next departures from nearest stops - DONE
    - Optional: if user profile exists, filter/sort by preferences - TODO
    """
    lat, lng = request.args.get("lat"), request.args.get("lng")
    if lat is None or lng is None:
        abort(404)
    stop_types = "NaptanMetroStation,NaptanRailStation"
    stops = get_stops(lat, lng, radius=2000, stop_types=stop_types)
    departures_tuple_list = get_departures_for_stops(stops)
    # departures_dicts = dumps
    resp = Response(dumps(departures_tuple_list))
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET"
    resp.headers["Access-Control-Allow-Header"] = "*"
    return resp


if __name__ == "__main__":
    app.run()
