from json import dumps
from flask import Flask, Response, request
from werkzeug.exceptions import abort

from helpers import get_stops, get_departures_for_stops

app = Flask(__name__)


@app.route("/")
def hello_world():  # put application's code here
    return "Hello World!"


@app.route("/nearest")
def nearest():
    """
    - Check cache - TODO
    - If not in cache, get stops within radius from TfL API - DONE
    - Return next departures from nearest stops - DONE
    - Optional: if user profile exists, filter/sort by preferences - TODO
    """
    lat, lon = request.args.get("lat"), request.args.get("lon")
    if lat is None or lon is None:
        abort(404)
    stops = get_stops(lat, lon, radius=1200)
    departures_tuple_list = get_departures_for_stops(stops)
    # departures_dicts = dumps
    resp = Response(dumps(departures_tuple_list))
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET"
    resp.headers["Access-Control-Allow-Header"] = "*"
    return resp


if __name__ == "__main__":
    app.run()
