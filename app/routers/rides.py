from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import RideRequest, RideResponse, Location
from app.db.mongodb import get_database
from app.services.pricing import calculate_dynamic_price
from app.services.matching_algo import haversine
from app.core.config import settings
import uuid
from datetime import datetime

router = APIRouter()

# --- CONSTANTS ---
MAX_TRUNK_CAPACITY = 4  # Max luggage items a standard car can hold

@router.post("/book", response_model=RideResponse)
async def book_ride(request: RideRequest, db=Depends(get_database)):
    rides_collection = db["active_rides"]
    
    # 1. DSA Approach: Geospatial Search for nearby active rides (Shared Pool)
    # We look for a ride within 2km radius that matches BOTH Seat AND Luggage constraints
    nearby_rides = await rides_collection.find({
        "location": {
            "$near": {
                "$geometry": {
                    "type": "Point",
                    "coordinates": [request.pickup_location.lng, request.pickup_location.lat]
                },
                "$maxDistance": 2000 # 2km radius
            }
        },
        "status": "WAITING",
        "available_seats": {"$gte": request.seats_needed},
        # STRICT LUGGAGE LOGIC: Current luggage must be low enough to fit new luggage
        "current_luggage_count": {"$lte": MAX_TRUNK_CAPACITY - request.luggage_count}
    }).to_list(length=10)
    
    matched_ride = None
    
    # 2. Greedy Matching Logic
    for ride in nearby_rides:
        # Check destination similarity (vector alignment) - simplified as distance here
        ride_dest = Location(lat=ride['destination']['lat'], lng=ride['destination']['lng'])
        dist_to_dest = haversine(request.dropoff_location, ride_dest)
        
        if dist_to_dest < 5.0: # If dropoffs are within 5km
            matched_ride = ride
            break
    
    if matched_ride:
        # 3. Concurrency Handling: Atomic Update (FindAndModify)
        # Prevents race condition where two users grab the last seat OR last trunk space
        updated_ride = await rides_collection.find_one_and_update(
            {
                "_id": matched_ride["_id"], 
                "available_seats": {"$gte": request.seats_needed},
                "current_luggage_count": {"$lte": MAX_TRUNK_CAPACITY - request.luggage_count}
            },
            {
                "$inc": {
                    "available_seats": -request.seats_needed,
                    "current_luggage_count": request.luggage_count
                },
                "$push": {
                    "passengers": request.user_id,
                    "stops": request.dropoff_location.model_dump()
                }
            },
            return_document=True
        )
        
        if updated_ride:
            return RideResponse(
                ride_id=str(updated_ride["_id"]),
                status="MATCHED",
                estimated_price=calculate_dynamic_price(100, 1.2, 0),
                passengers=updated_ride["passengers"],
                stops=[Location(**s) for s in updated_ride["stops"]]
            )

    # 4. No match found? Create new Ride
    new_ride = {
        "_id": str(uuid.uuid4()),
        "driver_id": "driver_" + str(uuid.uuid4())[:8],
        "passengers": [request.user_id],
        "available_seats": 4 - request.seats_needed, # Assuming 4 seater
        "current_luggage_count": request.luggage_count, # Initialize luggage
        "status": "WAITING",
        "location": {"type": "Point", "coordinates": [request.pickup_location.lng, request.pickup_location.lat]},
        "destination": request.dropoff_location.model_dump(),
        "stops": [request.dropoff_location.model_dump()],
        "created_at": datetime.utcnow()
    }
    
    await rides_collection.insert_one(new_ride)
    
    return RideResponse(
        ride_id=new_ride["_id"],
        status="CREATED_NEW",
        estimated_price=calculate_dynamic_price(150, 1.0, 0), # Higher price for solo start
        passengers=new_ride["passengers"],
        stops=[Location(**s) for s in new_ride["stops"]]
    )

@router.post("/cancel/{ride_id}")
async def cancel_ride(ride_id: str, user_id: str, db=Depends(get_database)):
    rides_collection = db["active_rides"]

    # 1. Find the ride and remove the passenger atomically
    # Note: In a real prod system, we'd need to know exactly how much luggage THIS user had
    # to decrement strictly. For this assignment, we assume 1 seat = 1 passenger removal.
    result = await rides_collection.find_one_and_update(
        {"_id": ride_id, "passengers": user_id},
        {
            "$pull": {"passengers": user_id},
            "$inc": {"available_seats": 1} 
            # Ideally: "$inc": {"current_luggage_count": -user_luggage} (requires storing metadata)
        },
        return_document=True
    )

    if not result:
        raise HTTPException(status_code=404, detail="Ride not found or user not in ride")

    # 2. If ride is now empty, mark it as CANCELLED or delete it
    if len(result["passengers"]) == 0:
        await rides_collection.update_one(
            {"_id": ride_id},
            {"$set": {"status": "CANCELLED"}}
        )
        return {"status": "Ride cancelled completely (no passengers left)"}

    return {"status": "Passenger removed", "remaining_passengers": result["passengers"]}