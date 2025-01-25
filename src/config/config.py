import logging

from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    LogLevel: int = logging.INFO
    LogFormat: str = "%(message)s"
    LogFileSizeMB: int = 50
    LogFileCount: int = 50

    SQLITE_DB_PATH: str = 'test_results.db'

    DB_HOST: str = 'localhost'
    DB_PORT: int = 5432
    DB_DATABASE: str = 'postgres'
    DB_USER: str = 'postgres'
    DB_PASSWORD: str = 'mysecretpassword'
    DB_DIALECT: str = 'postgresql+psycopg'

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


settings = Settings()

DB_URL = f'{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_DATABASE}'
