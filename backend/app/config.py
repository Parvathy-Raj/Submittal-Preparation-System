from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://submittals:change-me@localhost:5432/submittals"
    jwt_secret: str = "development-only-secret"
    jwt_minutes: int = 480
    bootstrap_admin_email: str = "admin@example.com"
    bootstrap_admin_password: str = "ChangeMe123!"
    max_upload_mb: int = 100
    max_package_source_mb: int = 60
    cors_origins: str = "http://localhost:5173,http://localhost:8080"
    cors_origin_regex: str | None = None
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def origins(self) -> list[str]:
        return [value.strip() for value in self.cors_origins.split(",")]


settings = Settings()
