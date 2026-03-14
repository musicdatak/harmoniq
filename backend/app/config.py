from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://harmoniq:harmoniq@db:5432/harmoniq"
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    CORS_ORIGINS: str = "http://localhost:5173"
    MAX_AUDIO_FILE_SIZE_MB: int = 50
    MUSICBRAINZ_USER_AGENT: str = "HarmoniQ/1.0.0 (contact@harmoniq.app)"
    GETSONGBPM_API_KEY: str = ""
    RAPIDAPI_KEY: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
