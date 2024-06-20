from pydantic import BaseModel
from typing import Tuple


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
