import requests
import time
from navigation.config import MAPBOX_TOKEN


# ----------- GEOCODING -----------
def geocode(place):
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{place}.json"

    params = {
        "access_token": MAPBOX_TOKEN
    }

    for attempt in range(3):
        try:
            res = requests.get(url, params=params, timeout=10)
            data = res.json()

            coords = data["features"][0]["center"]
            return coords[1], coords[0]

        except Exception as e:
            print(f"GEOCODE ERROR (attempt {attempt+1}):", e)
            time.sleep(2)

    return None


# ----------- ROUTING -----------
def get_route(start, end):
    url = f"https://api.mapbox.com/directions/v5/mapbox/walking/{start[1]},{start[0]};{end[1]},{end[0]}"

    params = {
        "access_token": MAPBOX_TOKEN,
        "geometries": "geojson",
        "steps": "true"
    }

    for attempt in range(3):
        try:
            res = requests.get(url, params=params, timeout=10)
            data = res.json()

            route = data["routes"][0]

            return {
                "distance": route["distance"],
                "duration": route["duration"],
                "steps": route["legs"][0]["steps"]
            }

        except Exception as e:
            print(f"ROUTE ERROR (attempt {attempt+1}):", e)
            time.sleep(2)

    return None