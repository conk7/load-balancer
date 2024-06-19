from pydantic import BaseModel
from pydantic_settings import BaseSettings
from typing import Tuple

class ServerConfig(BaseSettings):
    HOST = '127.0.0.1'
    BASE_PORT = 8080
    MAX_PORT = 65535
    PROCESS_CREATION_TIMEOUT_SEC = 2


class Task(BaseModel):
    type: str
    n: int


class CompletedTask(BaseModel):
    result: int


class ServerInfo(BaseModel):
    numOfServers: int
    numOfCompletedTasks: Tuple[int]

class newServerInfo(BaseModel):
    type: str
    n: int