from pydantic_settings import BaseSettings

class Settings(BaseSettings):
      rapidapi_key: str = "your_rapidapi_key_here"
      rapidapi_host: str = "linkedin-data-api.p.rapidapi.com"
      base_url: str = "https://linkedin-data-api.p.rapidapi.com"
      cache_ttl: int = 300
      rate_limit: str = "100/minute"
      api_secret_key: str = "changeme-in-production"

    class Config:
              env_file = ".env"
              env_file_encoding = "utf-8"

settings = Settings()
