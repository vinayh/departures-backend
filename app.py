from flask import Flask, request
from werkzeug.exceptions import abort

from helpers import get_stops, get_stop_with_departures

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
    return get_stop_with_departures(stops)


if __name__ == "__main__":
    app.run()
