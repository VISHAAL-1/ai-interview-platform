import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    GEMINI_API_KEY: str
    GOOGLE_APPLICATION_CREDENTIALS: str

    OPENSMILE_PATH: str
    OPENSMILE_CONFIG_PATH: str

    class Config:
        env_file = ".env"

settings = Settings()
