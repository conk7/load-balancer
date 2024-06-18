import signal
import uvicorn
import requests

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from .utils import (
    BASE_PORT, 
    HOST, 
    MAX_PORT, 
    PROCESS_CREATION_TIMEOUT_SEC, 
    newServerInfo
)
from multiprocessing import Process
from time import sleep
from os import kill
from typing import List, Dict, Any


load_balancer = FastAPI()
servers_ips: List[str] = []
next_server_id = 0
# server_app_name = 'src.server:server'


def is_port_in_use(port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def createWebServer(server_app_name: str) -> None:
    if len(servers_ips) == 0:
        port = BASE_PORT + 1
    else:
        port = int((servers_ips[-1])[-4:]) + 1
        if is_port_in_use(port):
            while is_port_in_use(port) and port <= MAX_PORT:
                port += 1
    if port == MAX_PORT + 1:
        raise Exception('No unused ports found')

    proc = Process(target=uvicorn.run, kwargs={'app': server_app_name, 'port': port})
    proc.start()
    
    total_time_slept = 0
    while not proc.is_alive() and time_slept < PROCESS_CREATION_TIMEOUT_SEC:
        time_slept = 0.05
        sleep(time_slept)
        total_time_slept += time_slept
    if(total_time_slept > 2):
        raise Exception('Could not start the server process')
        
    servers_ips.append(f'{HOST}:{port}')


@load_balancer.post('/api/private/addNewCopy')
def addNewServerCopy(data: newServerInfo) -> Dict[str, str]:
    if data.n <= 0:
        result = {
        'status': 'failure',
        'detail': 'Invalid argument: n'
        }
        return result
    
    for _ in range(data.n):
        try:
            createWebServer(data.type)
        except Exception('No unused ports found'):
            print('No unused ports found')
            result = {
                'status': 'failure',
                'detail': 'No unused ports found'
            }
            return result
        except Exception('Could not start the server process'):
            print('Could not create a server')
            result = {
                'status': 'failure',
                'detail': 'Could not start the server process'
            }
            return result

    result = {
        'status': 'success',
        'detail': f'Successfully added {data.n} server copies'
    }
    return result


@load_balancer.post('/api/private/deleteCopy') 
def deleteServerCopy(data: newServerInfo) -> Dict[str, str]:
    if data.n <= 0:
        result = {
            'status': 'failure',
            'detail': 'Invalid argument: n'
        }
        return result
    
    for _ in range(data.n):
        if len(servers_ips) == 0:
            print('No server copies to delete')
            result = {
                'status': 'failure',
                'detail': 'No server copies to delete'
            }
            return result
    
        ip = servers_ips.pop()
        request = requests.get(f'http://{ip}/api/getInfoInternal').json()
        kill(request['pid'], signal.SIGTERM)

    result = {
        'status': 'success',
        'detail': f'Successfully deleted {data.n} server copies'
    }
    return result

@load_balancer.get('/api/public/getInfo')
def getInfo() -> Dict[str, Any]:
    task_info_per_server = []

    for i, ip in enumerate(servers_ips, 1):
        request = requests.get(f'http://{ip}/api/getInfoInternal').json()
        task_info_per_server.append((f'Server #{i}', request['numOfCompletedTasks']))

    info = {
        'numOfServers': len(servers_ips),
        'numOfCompletedTasks': tuple(task_info_per_server)
    }
    
    return info


@load_balancer.post('/api/private/sendTask')
def resendTask() -> RedirectResponse:
    if len(servers_ips) == 0:
        raise HTTPException(
            status_code=503, 
            detail='No servers available'
        )

    global next_server_id
    next_server_id = (next_server_id) % (len(servers_ips)) 
    ip = servers_ips[next_server_id]
    next_server_id = (next_server_id + 1) % (len(servers_ips))

    return RedirectResponse(f'http://{ip}/api/sendTask', status_code=307)
