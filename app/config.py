from pydantic import field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Project List"
    database_url: str = "sqlite:///./test.db"
    debug: bool = True
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = [
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8080",
        "http://localhost:8080",
    ]
    cors_origin_regex: str = (
        r"^https?://("
        r"localhost|"
        r"127(?:\.\d{1,3}){3}|"
        r"192\.168(?:\.\d{1,3}){2}|"
        r"10(?:\.\d{1,3}){3}|"
        r"172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2}"
        r")(?::\d+)?$"
    )
    static_dir: str = "static"
    image_dir: str = "static/images"

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug_value(cls, value):
        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            normalized = value.strip().lower()

            if normalized in {"1", "true", "yes", "on", "debug", "development", "dev"}:
                return True

            if normalized in {"0", "false", "no", "off", "release", "production", "prod"}:
                return False

        return value

    class Config:
        env_file = ".env"

settings = Settings()
