from json import dumps
import azure.functions as func
import logging

from helpers import get_stops, get_departures_for_stops

app = func.FunctionApp()

@app.route(route="nearest", auth_level=func.AuthLevel.ANONYMOUS)
def nearest(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Request params:", req.params)

    lat, lng = req.params.get("lat"), req.params.get("lng")
    if not (lat and lng):
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            lat, lng = req_body.get("lat"), req_body.get("lng")

    stop_types = "NaptanMetroStation,NaptanRailStation"
    stops = get_stops(lat, lng, radius=2000, stop_types=stop_types)
    departures_tuple_list = get_departures_for_stops(stops)

    headers = {}
    headers["Access-Control-Allow-Origin"] = "*"
    headers["Access-Control-Allow-Methods"] = "GET"
    headers["Access-Control-Allow-Header"] = "*"
    return func.HttpResponse(dumps(departures_tuple_list), headers=headers)

    # else:
    #     return func.HttpResponse(
    #         "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
    #         status_code=200,
    #     )


if __name__ == "__main__":
    app.run()