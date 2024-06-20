import logging

from fastapi import FastAPI, HTTPException
from ..utils import (
    Task, 
    CompletedTask, 
    ServerInfo
)
from os import getpid
from http import HTTPStatus

server = FastAPI()
numOfCompletedTasks = 0
logger = logging.getLogger('load_balancer')
logging.basicConfig(filename='./src/server/server.log', level=logging.INFO)
logger.info('\n\nStarted')

def generate_nth_fibonacci(n: int) -> int:
    if(n <= 0):
        return -1
    
    count = 0
    num_next = 0
    num1 = 0
    num2 = 1
    while count < n - 1:
       num_next = num1 + num2
       num1 = num2
       num2 = num_next
       count += 1
    return num1


def generate_n_factorial(n: int) -> int:
    if(n < 0):
        return -1
    elif n == 0:
        return 1
    
    result = 1
    for i in range(1, n + 1):
        result *= i

    return result


@server.get('/api/getInfoInternal')
def getInfo() -> ServerInfo:
    pid = getpid()
    logger.info('Successfully collected and sent server info')
    logger.info(f'Info contained:\n Number of complited tasks{numOfCompletedTasks}\n server pid:{pid}')
    return ServerInfo(numOfCompletedTasks = numOfCompletedTasks, pid = pid)


@server.post('/api/sendTask') 
def handleTask(task: Task) -> CompletedTask:
    result = 0
    match task.type:
        case 'generate_nth_fibonacci':
            result = generate_nth_fibonacci(task.n)
        case 'generate_n_factorial':
            result = generate_n_factorial(task.n)
        case _:
            logger.info('Encountered exception: Not Implemented\n')
            logger.info(f'Info of the task that caused the exception:\n type: {task.type}\n n {task.type}')
            raise HTTPException(
                status_code=HTTPStatus.NOT_IMPLEMENTED, 
                detail='No method available to handle the task'
            )

    completed_task = CompletedTask(result=result)
    global numOfCompletedTasks 
    numOfCompletedTasks += 1
    logger.info(f'Successfully handled the task')
    logger.info(f'Info of the task:\n type: {task.type}\n n {task.type}')
    return completed_task