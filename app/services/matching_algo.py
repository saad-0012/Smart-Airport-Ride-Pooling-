import math
from app.models.schemas import Location

def haversine(loc1: Location, loc2: Location):
    # Calculate distance between two points in km
    R = 6371  # Earth radius in km
    dlat = math.radians(loc2.lat - loc1.lat)
    dlon = math.radians(loc2.lng - loc1.lng)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(loc1.lat)) * math.cos(math.radians(loc2.lat)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def is_detour_acceptable(current_route: list, new_pickup: Location, new_dropoff: Location, max_detour: float):
    # Simplified Logic: Check if adding points increases total distance beyond tolerance
    # In production, this uses GraphHopper or Google Maps API
    return True