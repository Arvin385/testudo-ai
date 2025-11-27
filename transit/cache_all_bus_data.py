import json
import math
import requests
import time

API = {
    "listRoutes": "https://api.umd.io/v1/bus/routes",
    "listSpecificRoute": "https://api.umd.io/v1/bus/routes/{route_id}",
    "listStops": "https://api.umd.io/v1/bus/stops",
    "listSpecificStop": "https://api.umd.io/v1/bus/stops/{stop_id}",
    "listBusLocationsByRoute": "https://api.umd.io/v1/bus/routes/{route_id}/locations",
    "busSchedules":"https://api.umd.io/v1/bus/routes/{route_id}/schedules",
    "getArrivalsForStop":"https://api.umd.io/v1/bus/routes/{route_id}/arrivals/{stop_id}",
}

def cache_all_bus_data():
    """
    Cache all bus data into a single file 'cached_data.json' using the new structure:

    {
      "<route_id>": {
         "directions": {
            "<direction_id>": {
               "title": "...",
               "stops": {
                  "<stop_id>": { "title": "...", "lat": ..., "lon": ..., "time": ... },
                  ...
               }
            },
            ...
         }
      },
      ...
    }
    """
    print("Starting to cache all bus data (with inbound/outbound directions)...")
    routesIds = []
    cached_data = {}

    try:
        routes_response = requests.get(API["listRoutes"], timeout=15)
        routes_response.raise_for_status()
        routes = routes_response.json()
        routesIds = [route["route_id"] for route in routes]
    except Exception as e:
        raise RuntimeError(f"Failed to fetch routes: {e}")

    def haversine_m(lat1, lon1, lat2, lon2):
        R = 6371000.0
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        return 2 * R * math.asin(min(1, math.sqrt(a)))

    for route_id in routesIds:
        print(f"  Caching route {route_id}...")
        try:
            route_response = requests.get(API["listSpecificRoute"].format(route_id=route_id), timeout=15)
            route_response.raise_for_status()
            route_data = route_response.json()[0]
        except Exception as e:
            print(f"    Warning: Failed to fetch data for route {route_id}: {e}")
            continue

        directions = route_data.get("directions", [])
        if not directions:
            continue

        route_entry = {"directions": {}}

        for direction in directions:
            direction_id = direction.get("direction_id")
            title = direction.get("title", "")
            stop_ids = direction.get("stops", [])

            if not stop_ids:
                continue

            stops_list = []
            for stop_id in stop_ids:
                try:
                    stop_resp = requests.get(API["listSpecificStop"].format(stop_id=stop_id), timeout=15)
                    stop_resp.raise_for_status()
                    stop_data = stop_resp.json()[0]
                    stops_list.append(stop_data)
                except Exception as e:
                    print(f"    Warning: failed to fetch stop {stop_id} for {route_id}/{direction_id}: {e}")

            stops_dict = {}
            num_stops = len(stops_list)
            if num_stops < 2:
                continue

            # compute per-stop travel time (including last -> first to close the loop)
            for i, stop in enumerate(stops_list):
                stop_id = stop.get("stop_id")
                title = stop.get("title")
                lat = stop.get("lat")
                lon = stop.get("long")

                if not stop_id or lat is None or lon is None:
                    continue

                # wrap around for last stop (looping route)
                next_stop = stops_list[(i + 1) % num_stops]
                next_lat = next_stop.get("lat")
                next_lon = next_stop.get("long")

                try:
                    dist_m = haversine_m(lat, lon, next_lat, next_lon)
                    time_to_next = round(dist_m / 6.7056, 1)
                except Exception:
                    time_to_next = 0.0

                stops_dict[stop_id] = {
                    "title": title,
                    "lat": lat,
                    "lon": lon,
                    "time": time_to_next
                }

            route_entry["directions"][direction_id] = {
                "title": title,
                "stops": stops_dict
            }

        if route_entry["directions"]:
            cached_data[route_id] = route_entry

        time.sleep(0.2)

    try:
        with open("cached_data.json", "w", encoding="utf-8") as f:
            json.dump(cached_data, f, ensure_ascii=False, indent=2)
        print(f"Cached data written successfully to 'cached_data.json' ({len(cached_data)} routes).")
    except Exception as e:
        raise RuntimeError(f"Failed to write cached data to file: {e}")
    
if __name__ == "__main__":
    cache_all_bus_data()
    print("Yippee! Successful caching completed")