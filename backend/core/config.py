"""
core/config.py
Lee las variables de entorno del archivo .env y las expone
como un objeto tipado. Pydantic valida que existan y tengan el tipo correcto.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "fine_shoes"
    DB_USER: str = "root"
    DB_PASSWORD: str = ""

    JWT_SECRET: str = "dev_secret_change_in_production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

    FRONTEND_URL: str = "http://localhost:5500"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Instancia única — se importa desde cualquier módulo
settings = Settings()
