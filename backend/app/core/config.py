from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    serpapi_key: str = ""
    anthropic_api_key: str = ""
    amazon_domain: str = "amazon.in"
    default_category: str = "wireless earphones"
    serpapi_cache_ttl: int = 900
    serpapi_max_pages: int = 3
    frontend_origin: str = "http://localhost:5173"


settings = Settings()
