from flask import Flask, Response, request
from werkzeug.exceptions import abort

from nearest import nearest_departures_json

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
    stop_types = request.args.get("stopTypes") # Optional
    modes = request.args.get("modes") # Optional
    if lat is None or lng is None:
        abort(404)

    resp = Response(nearest_departures_json(lat, lng, stop_types, modes), mimetype='application/json')
    resp.headers['Content-Type'] = 'application/json'
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET"
    resp.headers["Access-Control-Allow-Header"] = "*"
    return resp


if __name__ == "__main__":
    app.run()
