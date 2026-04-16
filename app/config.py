from pydantic import field_validator
from pydantic_settings import BaseSettings
import dotenv
import os

dotenv.load_dotenv()

class Settings(BaseSettings):
    app_name: str = "Project List"
    database_url: str = f"postgresql+psycopg2://{os.getenv('password')}:{os.getenv('password')}@{os.getenv('host')}:{os.getenv('port')}/{os.getenv('database')}"
    debug: bool = True
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = ["*"]
    cors_origin_regex: str = ".*"
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
