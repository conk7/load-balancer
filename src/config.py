from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    HOST: str = '127.0.0.1'
    BASE_PORT: int = 8080
    MAX_PORT: int = 65535
    PROCESS_CREATION_TIMEOUT_SEC: int = 2
