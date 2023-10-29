import os
import requests

STOPPOINT_ENDPOINT = "https://api.tfl.gov.uk/StopPoint"

SECRETS_TO_PATHS = {
    "FLASK_SECRET_KEY": Path(".secrets/flask_secret_key"),
    "TFL_APP_ID": Path(".secrets/tfl_app_id"),
    "TFL_APP_KEY": Path(".secrets/tfl_app_key"),
    # 'GOOGLE_CLIENT_ID': Path('.secrets/google_client_id'),
    # 'GOOGLE_CLIENT_SECRET': Path('.secrets/google_client_secret'),
    # 'DATABASE_URL': Path('.secrets/database_url')
}


class Departure:
    stop_id = None


class Stop:
    lat: float = None
    lon: float = None
    id: int = None

    def departures(self) -> list[Departure]:
        pass


def get_secret(name: str):
    env_name = os.getenv("DEPARTURES_ENV")
    if env_name == "RENDER":
        return get_secret_file(SECRETS_TO_PATHS[name].relative_to(".secrets"))
    elif env_name == "FLY":
        if name in os.environ:
            return os.getenv(name)
        else:
            raise Exception
    else:
        return get_secret_file(SECRETS_TO_PATHS[name])


def get_secret_file(path) -> str:
    try:
        with path.open("r") as f:
            return f.read()
    except:
        exit(f"Error getting secret {path}")


def get_stops(lat: float, lon: float) -> list[Stop]:
    pass
