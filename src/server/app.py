import uvicorn

from fastapi import FastAPI
from multiprocessing import Process
from time import sleep
from ..config import (
    Settings
)
from typing import List

ServerSettings = Settings()


def is_port_in_use(port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((ServerSettings.HOST, port)) == 0


def createWebServer(server_app_name: str, server_ips: List[str]) -> str:
    if len(server_ips) == 0:
        port = ServerSettings.BASE_PORT + 1
    else:
        port = int((server_ips[-1])[-4:]) + 1
        if is_port_in_use(port):
            while is_port_in_use(port) and port <= ServerSettings.MAX_PORT:
                port += 1
    if port == ServerSettings.MAX_PORT + 1:
        raise Exception('No unused ports found')

    proc = Process(target=uvicorn.run, kwargs={'app': server_app_name, 'port': port})
    proc.start()
    
    total_time_slept = 0
    while not proc.is_alive() and time_slept < ServerSettings.PROCESS_CREATION_TIMEOUT_SEC:
        time_slept = 0.05
        sleep(time_slept)
        total_time_slept += time_slept
    if(total_time_slept > 2):
        raise Exception('Could not start the server process')
        
    return f'{ServerSettings.HOST}:{port}'