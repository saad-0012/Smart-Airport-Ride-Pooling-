from pydantic import BaseModel, Field
from typing import List, Optional, Tuple
from datetime import datetime

class Location(BaseModel):
    lat: float
    lng: float

class RideRequest(BaseModel):
    user_id: str
    pickup_location: Location
    dropoff_location: Location
    seats_needed: int = 1
    luggage_count: int = 0

class RideResponse(BaseModel):
    ride_id: str
    driver_id: str = "assigning..."
    status: str
    estimated_price: float
    passengers: List[str]
    stops: List[Location]