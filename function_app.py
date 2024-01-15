import azure.functions as func
import logging

from helpers import nearest_departures_json

app = func.FunctionApp()


@app.route(route="nearest", auth_level=func.AuthLevel.ANONYMOUS)
def nearest(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Request params:", req.params)

    lat, lng = req.params.get("lat"), req.params.get("lng")
    stop_types = req.params.get("stopTypes")

    if lat is None or lng is None:
        return func.HttpResponse("Lat and lng not provided.", status_code=400)
    
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET",
        "Access-Control-Allow-Header": "*",
    }
    
    return func.HttpResponse(nearest_departures_json(lat, lng, stop_types=stop_types), headers=headers)


if __name__ == "__main__":
    app.run()
