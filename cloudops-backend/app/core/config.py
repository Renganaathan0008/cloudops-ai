from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "CloudOps AI Backend"
    environment: str = "development"

    database_url: str = "postgresql+psycopg2://cloudops@localhost:5432/cloudops"

    jwt_secret_key: str = "change-me-in-env"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    prometheus_url: str = "http://localhost:9090"


settings = Settings()
