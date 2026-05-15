from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://marlowe:marlowe@localhost:5432/marlowe"
    redis_url: str = "redis://localhost:6379"
    anthropic_api_key: str = ""

    model_config = {"env_file": ".env"}


settings = Settings()
