from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "CloudOps AI Backend"
    environment: str = "development"

    database_url: str = "postgresql+psycopg2://cloudops@localhost:5432/cloudops"
    database_host: str | None = None
    database_port: int = 5432
    database_name: str | None = None
    database_user: str | None = None
    database_password: str | None = None

    jwt_secret_key: str = "change-me-in-env"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    prometheus_url: str = "http://localhost:9090"

    @property
    def sqlalchemy_database_url(self) -> str:
        """Return a SQLAlchemy URL from discrete Docker DB settings or DATABASE_URL."""

        if self.database_host is None:
            return self.database_url

        required = (
            self.database_name,
            self.database_user,
            self.database_password,
        )
        if any(value is None for value in required):
            raise ValueError(
                "DATABASE_NAME, DATABASE_USER, and DATABASE_PASSWORD are required "
                "when DATABASE_HOST is set"
            )

        return URL.create(
            drivername="postgresql+psycopg2",
            username=self.database_user,
            password=self.database_password,
            host=self.database_host,
            port=self.database_port,
            database=self.database_name,
        ).render_as_string(hide_password=False)


settings = Settings()
