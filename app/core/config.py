from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    EMAIL_USER: str
    EMAIL_PASS: str

    class Config:
        env_file = ".env"  # Load variables from .env file

settings = Settings()
