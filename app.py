from json import dumps
from flask import Flask, Response, request
from werkzeug.exceptions import abort

from helpers import nearest_departures

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
    stop_types = request.args.get("stopTypes")
    if lat is None or lng is None:
        abort(404)

    resp = Response(dumps(nearest_departures(lat, lng, stop_types=stop_types)))
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET"
    resp.headers["Access-Control-Allow-Header"] = "*"
    return resp


if __name__ == "__main__":
    app.run()
