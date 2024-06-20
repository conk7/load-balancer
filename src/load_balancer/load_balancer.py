import signal
import requests
import logging

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from ..utils import (
    newServerInfo
)
from ..server.app import createWebServer
from os import kill
from typing import List, Dict, Any


load_balancer = FastAPI()
server_ips: List[str] = []
next_server_id = 0
logger = logging.getLogger('load_balancer')
logging.basicConfig(filename='./src/load_balancer/load_balancer.log', level=logging.INFO)


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
            new_server_ip = createWebServer(data.type, server_ips)
            server_ips.append(new_server_ip)
        except Exception('No unused ports found'):
            logger.info(f'Encountered exception: No unused ports found\n {data}')

            result = {
                'status': 'failure',
                'detail': 'No unused ports found'
            }
            return result
        except Exception('Could not start the server process'):
            logger.info(f'Encountered exception: Could not start the server process\n {data}')
            result = {
                'status': 'failure',
                'detail': 'Could not start the server process'
            }
            return result

    result = {
        'status': 'success',
        'detail': f'Successfully added {data.n} server copies'
    }
    logger.info(f'Successfully handled the request\n {result}')
    return result


@load_balancer.post('/api/private/deleteCopy') 
def deleteServerCopy(data: newServerInfo) -> Dict[str, str]:
    if data.n <= 0:
        logger.info(f'Encountered exception: No servers found\n {data}')
        raise HTTPException(status_code=404, detail="No servers found")
    
    for _ in range(data.n):
        if len(server_ips) == 0:
            logger.info(f'Encountered exception: No servers found\n {data}')
            raise HTTPException(status_code=404, detail="No servers found")
    
        ip = server_ips.pop()
        request = requests.get(f'http://{ip}/api/getInfoInternal').json()
        kill(request['pid'], signal.SIGTERM)

    result = {
        'status': 'success',
        'detail': f'Successfully deleted {data.n} server copies'
    }
    logger.info(f'Successfully handled request\n {result}')
    return result


@load_balancer.get('/api/public/getInfo')
def getInfo() -> Dict[str, Any]:
    task_info_per_server = []

    for i, ip in enumerate(server_ips, 1):
        request = requests.get(f'http://{ip}/api/getInfoInternal').json()
        task_info_per_server.append((f'Server #{i}', request['numOfCompletedTasks']))

    info = {
        'numOfServers': len(server_ips),
        'numOfCompletedTasks': tuple(task_info_per_server)
    }
    logger.info(f'Successfully collected and sent info of each server\n {info}')
    return info


@load_balancer.post('/api/private/sendTask')
def resendTask() -> RedirectResponse:
    if len(server_ips) == 0:
        logger.info('Encountered exception: 503 No servers available')
        raise HTTPException(
            status_code=503, 
            detail='No servers available'
        )

    global next_server_id
    next_server_id = (next_server_id) % (len(server_ips)) 
    ip = server_ips[next_server_id]
    next_server_id = (next_server_id + 1) % (len(server_ips))
    logger.info(f'Successfully redirected request to {ip}')
    return RedirectResponse(f'http://{ip}/api/sendTask', status_code=307)
