from fastapi import FastAPI
from app.routers import rides
from app.db.mongodb import close_mongo_connection, connect_to_mongo

app = FastAPI(title="Airport Ride Pooling System", version="1.0.0")

app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("shutdown", close_mongo_connection)

app.include_router(rides.router, prefix="/api/v1", tags=["rides"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "latency": "low"}