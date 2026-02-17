# ✈️ Airport Ride Pooling Backend

A high-performance, concurrent backend system for grouping airport passengers into shared cabs. This system optimizes for minimal travel deviation, strict luggage constraints, and real-time concurrency safety.

## 🛠️ Tech Stack
* **Language:** Python 3.11
* **Framework:** FastAPI (High-performance Async I/O)
* **Database:** MongoDB (Motor Async Driver)
* **Infrastructure:** Docker & Docker Compose
* **Validation:** Pydantic V2

## 🚀 Setup & Execution

### Option 1: Docker (Recommended)
This method automatically sets up the API and the Database in an isolated network.

1.  **Build and Start:**
    ```bash
    docker-compose up --build
    ```
2.  **Verify Status:**
    The API will launch at `http://localhost:8000`.

### Option 2: Manual / Local
1.  Ensure **MongoDB** is running locally on port `27017`.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Run the server:
    ```bash
    uvicorn app.main:app --reload
    ```

---

## 🧪 How to Test (API Documentation)

The project includes interactive **Swagger/OpenAPI** documentation.

1.  Open your browser to: **[http://localhost:8000/docs](http://localhost:8000/docs)**
2.  You will see three endpoints:
    * `GET /health`: System health check.
    * `POST /api/v1/book`: Request a ride.
    * `POST /api/v1/cancel/{ride_id}`: Cancel a booking.

### 📝 Sample Test Data

**1. Booking a Ride (Copy-Paste into Swagger):**
```json
{
  "user_id": "user_alpha",
  "pickup_location": {
    "lat": 12.9716,
    "lng": 77.5946
  },
  "dropoff_location": {
    "lat": 12.9352,
    "lng": 77.6245
  },
  "seats_needed": 1,
  "luggage_count": 2
}