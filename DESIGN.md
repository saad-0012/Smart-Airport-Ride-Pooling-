***

### 2. `DESIGN.md`
**Purpose:** Technical deep-dive, complexity analysis, and architecture decisions (Required for evaluation).

```markdown
# 📐 System Design & Architecture

## 1. High-Level Architecture (HLD)
The system is designed as a stateless microservice backed by a document store with geospatial capabilities.

graph TD
    User[📱 Mobile App / User] -->|HTTP/JSON| LB[⚖️ Load Balancer]
    LB --> API[🚀 FastAPI Backend Container]
    
    subgraph Docker Network
        API -->|Async Read/Write| DB[(🍃 MongoDB Cluster)]
        API -->|Logs| Logs[📄 Docker Logs]
    end
    
    DB -->|Geo-Index| GIS[🗺️ 2dsphere Index]
    
    style API fill:#00C853,stroke:#333,stroke-width:2px,color:white
    style DB fill:#1565C0,stroke:#333,stroke-width:2px,color:white

**Design Choices:**
* **FastAPI:** Chosen for native async support, crucial for handling 100+ concurrent requests per second without blocking I/O.
* **MongoDB 2dsphere:** Allows purely database-level geospatial filtering, reducing the data transfer overhead to the application layer.

## 2. Low-Level Design (LLD)

classDiagram
    class RideRequest {
        +str user_id
        +Location pickup
        +Location dropoff
        +int seats_needed
        +int luggage_count
    }
    class RideResponse {
        +str ride_id
        +str status
        +float price
        +List[str] passengers
    }
    class MatchingService {
        +find_nearby_rides()
        +calculate_detour()
        +haversine_distance()
    }
    class RideController {
        +book_ride()
        +cancel_ride()
    }

    RideController --> RideRequest : validates
    RideController --> MatchingService : uses
    RideController --> RideResponse : returns

### Data Models (Schema)
**Collection:** `active_rides`
```json
{
  "_id": "UUID",
  "driver_id": "String",
  "status": "WAITING | MATCHED | CANCELLED",
  "location": { "type": "Point", "coordinates": [lng, lat] },
  "destination": { "lat": Float, "lng": Float },
  "available_seats": Integer,
  "current_luggage_count": Integer,
  "passengers": ["user_id_1", "user_id_2"],
  "stops": [{ "lat": Float, "lng": Float }]
}

```

### Class Diagram / Modules

* **RideRequest (DTO):** Validates inputs (Seats > 0, Coordinates valid).
* **RideResponse (DTO):** Standardized API output.
* **MatchingService:** Contains the logic for `haversine` distance and filtering.

## 3. Algorithm & Complexity Analysis

### Problem: Real-time Ride Matching

We solve the "Nearest Neighbor with Constraints" problem.

**Approach: "Geospatial Filter + Greedy Selection"**

1. **Geospatial Filter (Database Layer):**
* We utilize MongoDB's `$near` operator on a `2dsphere` index.
* **Filter Criteria:** `Radius <= 2km` AND `Available Seats >= N` AND `Luggage Capacity >= M`.
* **Time Complexity:** **O(log M)**, where M is the total number of active rides. MongoDB uses S2 geometry cells for efficient indexing.


2. **Greedy Selection (Application Layer):**
* We fetch the top 10 candidates from the DB.
* We iterate through them to find the one with the minimal destination deviation (< 5km).
* **Time Complexity:** **O(K)**, where K is the limit (10). This is constant time.



**Total Complexity:** **O(log M)** per request.
This ensures the system scales to 10,000 users while maintaining <300ms latency.

## 4. Concurrency Handling Strategy

**Requirement:** Prevent double-booking (e.g., two users booking the last seat simultaneously).

**Solution: Optimistic Concurrency Control via Atomic Writes**
We do **not** use application-level mutexes (which don't scale across multiple containers). Instead, we use MongoDB's atomic `find_one_and_update`.

**The Query:**

```python
db.active_rides.find_one_and_update(
    filter={
        "_id": matched_ride_id,
        "available_seats": { "$gte": requested_seats }  # CRITICAL CHECK
    },
    update={
        "$inc": { "available_seats": -requested_seats }
    }
)

```

**Mechanism:**

1. The database locks the specific document.
2. It re-checks the `available_seats` condition.
3. If valid, it decrements the count and returns success.
4. If the condition fails (someone else took the seat milliseconds ago), it returns `None`.
5. If `None` is returned, the backend automatically falls back to creating a **New Ride**.

## 5. Dynamic Pricing Logic

Price is calculated at the moment of booking to account for demand.

`Price = Base Fare + (Demand Factor * 1.2) + (Distance Surcharge)`

* **Base Fare:** 100 units.
* **Shared Discount:** Pooling avoids the standard "Solo Rider" surcharge (1.5x), incentivizing grouping.

```

```