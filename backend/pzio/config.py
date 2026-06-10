import warnings
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_JWT_SECRET = "dev-secret-change-me-in-production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    database_url: str = "sqlite:///./pzio.db"

    jwt_secret: str = _DEFAULT_JWT_SECRET
    jwt_algorithm: str = "HS256"
    jwt_expires_min: int = 60

    cors_origins: str = "http://localhost:5173"

    frontend_url: str = "http://localhost:5173"

    # Directory where forced database backups (SAD §4.5 — POST /api/admin/backups) are stored.
    backup_dir: str = "./backups"
    upload_dir: str = "./uploads"

    max_file_size: int = 10 * 1024 * 1024  # 10 MB

    google_client_id: str | None = None
    google_client_secret: str | None = None
    
    github_client_id: str | None = None
    github_client_secret: str | None = None

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()

if settings.jwt_secret == _DEFAULT_JWT_SECRET:
    warnings.warn(
        "\n" + "-" * 85 + "\n" +
        f"JWT_SECRET is set to the known default value '{_DEFAULT_JWT_SECRET}'.\n"
        "This is REALLY INSECURE - set a unique random value in production."
        "\n" + "-" * 85,
        stacklevel=2,
    )
