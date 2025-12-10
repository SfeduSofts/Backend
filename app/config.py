from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Project List"
    database_url: str = "sqlite:///./test.db"
    debug: bool = True
    cors_origins: list[str] = []
    static_dir: str = "static"
    image_dir: str = "static/images"

    class Config:
        env_file = ".env"

settings = Settings()