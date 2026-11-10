from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Lufthansa Aviation Operations Platform"
    app_version: str = "0.1.0"
    environment: str = "development"
    database_url: str = "sqlite:///./aviation.db"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
