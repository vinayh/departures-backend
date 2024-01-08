from json import dumps
import azure.functions as func
import logging

from helpers import get_stops, get_departures_for_stops

app = func.FunctionApp()


@app.route(route="nearest", auth_level=func.AuthLevel.ANONYMOUS)
def nearest(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Request params:", req.params)

    lat, lng = req.params.get("lat"), req.params.get("lng")
    stop_types = (
        req.params.get("stopTypes")
        if "stopTypes" in req.params
        else "NaptanMetroStation,NaptanRailStation"
    )

    if not (lat and lng):
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            lat, lng = req_body.get("lat"), req_body.get("lng")

    stops = get_stops(lat, lng, radius=2000, stop_types=stop_types)
    stops_deps = get_departures_for_stops(stops)

    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET",
        "Access-Control-Allow-Header": "*",
    }
    
    return func.HttpResponse(dumps(stops_deps), headers=headers)


if __name__ == "__main__":
    app.run()
