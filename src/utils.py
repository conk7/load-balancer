from pydantic import BaseModel
from typing import Tuple


class Task(BaseModel):
    type: str
    n: int


class CompletedTask(BaseModel):
    result: int


class ServerInfo(BaseModel):
    numOfCompletedTasks: int
    pid: int


class newServerInfo(BaseModel):
    type: str
    n: int


class LoadBalancerInfo(BaseModel):
    numOfServers: int
    numOfCompletedTasks: Tuple[Tuple[str,int], ...]


class ServerCopyResponse(BaseModel):
    status: str
    detail: str
