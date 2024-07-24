import signal
import requests
import logging

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from ..utils import (
    newServerInfo,
    ServerCopyResponse,
    LoadBalancerInfo,
    ServerInfo
)
from http import HTTPStatus
from ..server.app import createWebServer
from os import kill
from typing import List
from pydantic_core import ValidationError


load_balancer = FastAPI()
server_ips: List[str] = []
next_server_id = 0
logger = logging.getLogger('load_balancer')
logging.basicConfig(filename='./src/load_balancer/load_balancer.log', level=logging.INFO)
logger.info('\n\nStarted')


@load_balancer.post('/api/private/addNewCopy')
async def addNewServerCopy(data: newServerInfo) -> ServerCopyResponse:
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
            logger.info(f'Encountered exception: No unused ports found. The task had the following params: \n {data}')

            result = {
                'status': 'failure',
                'detail': 'No unused ports found'
            }
            return result
        except Exception('Could not start the server process'):
            logger.info(f'Encountered exception: Could not start the server process. The task had the following params:\n {data}')
            result = {
                'status': 'failure',
                'detail': 'Could not start the server process'
            }
            return result

    logger.info(f'Successfully added {data.n} server copies')
    return ServerCopyResponse(status='success', detail=f'Successfully added {data.n} server copies')


@load_balancer.post('/api/private/deleteCopy') 
async def deleteServerCopy(data: newServerInfo) -> ServerCopyResponse:
    if data.n <= 0:
        logger.info('Encountered exception: No servers found\n')
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="No servers found")
    
    for _ in range(data.n):
        if len(server_ips) == 0:
            logger.info('Encountered exception: No servers found\n')
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="No servers found")
    
        ip = server_ips.pop()
        logger.info(requests.get(f'http://{ip}/api/getInfoInternal'))
        request = requests.get(f'http://{ip}/api/getInfoInternal').json()

        try:
            request = ServerInfo.model_validate(request)
        except ValidationError:
            logger.info('Received invalid data')
            return ServerCopyResponse(status='failure', detail='Could delete server copies')
        
        kill(request.pid, signal.SIGTERM)

    logger.info(f'Successfully deleted {data.n} server copies')
    return ServerCopyResponse(status='success', detail=f'Successfully deleted {data.n} server copies')


@load_balancer.get('/api/public/getInfo')
async def getInfo() -> LoadBalancerInfo:
    numOfCompletedTasks = []

    for i, ip in enumerate(server_ips, 1):
        request = requests.get(f'http://{ip}/api/getInfoInternal').json()

        try:
            request = ServerInfo.model_validate(request)
        except ValidationError:
            logger.info('Received invalid data')
            return LoadBalancerInfo(numOfServers = -1, numOfCompletedTasks = [])

        numOfCompletedTasks.append((f'Server #{i}', request.numOfCompletedTasks))

    numOfServers = len(server_ips)

    logger.info('Successfully collected and sent info of each server')
    logger.info(f'Info:\n Number of active servers {numOfServers}')
    for server in numOfCompletedTasks:
        logger.info(f'{server[0]} successfully handled {server[1]} tasks')

    return LoadBalancerInfo(numOfServers = numOfServers, numOfCompletedTasks = numOfCompletedTasks)


@load_balancer.post('/api/private/sendTask')
async def resendTask() -> RedirectResponse:
    if len(server_ips) == 0:
        logger.info('Encountered exception: No servers available')
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE, 
            detail='No servers available'
        )

    global next_server_id
    next_server_id = (next_server_id) % (len(server_ips)) 
    ip = server_ips[next_server_id]
    next_server_id = (next_server_id + 1) % (len(server_ips))
    logger.info(f'Successfully redirected request to {ip}')
    return RedirectResponse(f'http://{ip}/api/sendTask', status_code=HTTPStatus.TEMPORARY_REDIRECT)
