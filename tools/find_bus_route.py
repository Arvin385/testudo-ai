from tools.tooling import Tool
from tools.tooling import tool

import requests
import time

def get_lat_lon_from_address(address: str) -> tuple[float, float]:
    """
    Fetches the latitude and longitude of an address using the
    OpenStreetMap Nominatim API.

    Args:
        address (str): The address or place name to look up.

    Returns:
        dict: A dictionary with latitude and longitude if found, e.g.:
              {"lat": 38.9869, "lon": -76.9426}
              or an error message if not found.

    Raises:
        requests.exceptions.RequestException: For network or HTTP errors.
    """
    base_url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": address,
        "format": "json",
        "limit": 1
    }

    # Include a custom User-Agent per OSM usage policy
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    
    response = requests.get(base_url, params=params, headers=headers, timeout=10)
    response.raise_for_status()

    data = response.json()
    if not data:
        raise Exception("Address not found.")

    # Return the first result
    result = data[0]
    return float(result["lat"]), float(result["lon"])

@tool
def find_bus_route(start_addr: str, dest_addr: str):
    """
    Determines the optimal bus route and direction between two addresses
    using pre-cached route data, minimizing total travel time (bus + walking).

    This function converts the provided start and destination addresses into
    geographic coordinates using the OpenStreetMap Nominatim API, then searches
    through all routes and directions stored in `cached_data.json` to identify
    the boarding and alighting stops that produce the shortest overall estimated
    travel time. The total travel time includes in-vehicle bus time as well as
    walking time to and from the stops.

    Routes that would require more than 1000 meters of total walking distance
    (start → boarding + alighting → destination) are excluded. The function
    supports circular (loop) bus routes by wrapping around the stop list when
    computing travel times between stops.

    Args:
        start_addr (str): The starting address or location name.
        dest_addr (str): The destination address or location name.

    Returns:
        dict: A dictionary describing the best-matching bus route and estimated
        travel details, or an error message if no suitable route is found.
    """
    import json
    import math
    
    start_lat, start_lon = get_lat_lon_from_address(start_addr)
    dest_lat, dest_lon = get_lat_lon_from_address(dest_addr)

    def haversine_m(lat1, lon1, lat2, lon2):
        R = 6371000.0
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi, dlambda = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        return 2 * R * math.asin(min(1, math.sqrt(a)))

    WALK_SPEED_M_S = 1.4  # walking speed for estimating walk time (m/s)

    # --- Load cached file ---
    try:
        with open('cached_data.json', 'r') as f:
            cached = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError("cached_data.json not found. Run cache_all_bus_data() first.")
    except Exception as e:
        raise RuntimeError(f"Failed to read cached_data.json: {e}")

    best_option = None
    best_score = math.inf

    # Iterate routes and their directions
    for route_id, route_data in cached.items():
        directions = route_data.get("directions", {})
        if not directions:
            continue

        for direction_id, direction_data in directions.items():
            stops_dict = direction_data.get("stops", {})
            if not stops_dict or not isinstance(stops_dict, dict):
                continue

            stop_ids = list(stops_dict.keys())
            stops = [stops_dict[sid] for sid in stop_ids]

            # find closest boarding and alighting stops (by walking distance)
            best_board_idx, best_alight_idx = None, None
            best_board_d, best_alight_d = math.inf, math.inf
            best_board, best_alight = None, None

            for i, s in enumerate(stops):
                lat, lon = s.get("lat"), s.get("lon")
                if lat is None or lon is None:
                    continue

                d_start = haversine_m(start_lat, start_lon, lat, lon)
                d_dest = haversine_m(dest_lat, dest_lon, lat, lon)

                if d_start < best_board_d:
                    best_board_d = d_start
                    best_board_idx = i
                    best_board = {
                        "stop_id": stop_ids[i],
                        "stop_name": s.get("title"),
                        "lat": lat,
                        "lon": lon,
                        "distance_m": round(d_start, 1)
                    }

                if d_dest < best_alight_d:
                    best_alight_d = d_dest
                    best_alight_idx = i
                    best_alight = {
                        "stop_id": stop_ids[i],
                        "stop_name": s.get("title"),
                        "lat": lat,
                        "lon": lon,
                        "distance_m": round(d_dest, 1)
                    }

            if best_board_idx is None or best_alight_idx is None:
                continue

            # Skip unrealistic walking legs (> 1 km total)
            total_walk_m = best_board_d + best_alight_d
            if total_walk_m > 1000:
                # too much walking, skip this route/direction
                continue

            # --- Sum bus travel time using per-segment times ---
            # times[i] = time from stop i -> next stop (seconds); assume cache stores that
            times = []
            for s in stops:
                t = s.get("time", 0)
                try:
                    times.append(float(t))
                except Exception:
                    times.append(0.0)

            n = len(times)
            if n == 0:
                continue

            # function to sum segments from idx a to idx b (not inclusive of b),
            # walking forward along the direction, wrapping if needed
            def sum_segments(a_idx, b_idx):
                if a_idx == b_idx:
                    # boarding and alighting are same stop: bus ride time = 0
                    return 0.0
                total = 0.0
                i = a_idx
                # iterate until we reach b_idx
                while i != b_idx:
                    total += times[i]  # time from stop i -> stop (i+1)%n
                    i = (i + 1) % n
                return total

            bus_time_s = sum_segments(best_board_idx, best_alight_idx)

            # --- walking times ---
            walk_time_to_board_s = best_board_d / WALK_SPEED_M_S
            walk_time_from_alight_s = best_alight_d / WALK_SPEED_M_S

            total_eta_s = bus_time_s + walk_time_to_board_s + walk_time_from_alight_s

            # Scoring: primarily by total ETA (seconds), tie-break with small distance penalty
            score = total_eta_s + (best_board_d + best_alight_d) / 100.0

            if score < best_score:
                best_score = score
                # build a helpful result
                best_option = {
                    "route_id": route_id,
                    "direction_id": direction_id,
                    "direction_name": direction_data.get("title"),
                    "boarding": best_board,
                    "alighting": best_alight,
                    "walking_distance_to_board_m": round(best_board_d, 1),
                    "walking_distance_from_alight_m": round(best_alight_d, 1),
                    "walking_time_to_board_s": round(walk_time_to_board_s, 1),
                    "walking_time_from_alight_s": round(walk_time_from_alight_s, 1),
                    "bus_time_s": round(bus_time_s, 1),
                    "estimated_travel_time_s": round(total_eta_s, 1),
                    "score": round(score, 1)
                }

    if best_option:
        return best_option

    return {"error": "No suitable route found."}

TOOL_SPEC = find_bus_route.tool_spec()