from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGO_URL: str
    DB_NAME: str
    PORT: int = 8000  # <--- Added this field to match .env
    MAX_DETOUR_KM: float = 2.0
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # <--- Safety net: ignores other random env vars instead of crashing

settings = Settings()