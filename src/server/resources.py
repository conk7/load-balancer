import logging

from fastapi import FastAPI, HTTPException
from ..utils import Task, CompletedTask
from os import getpid


server = FastAPI()
numOfCompletedTasks = 0
logger = logging.getLogger('load_balancer')
logging.basicConfig(filename='./src/server/server.log', level=logging.INFO)

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
def getInfo():
    info = {
        'numOfCompletedTasks': numOfCompletedTasks,
        'pid': getpid(),
    }
    logger.info(f'Successfully collected and sent server info\n {info}')
    return info


@server.post('/api/sendTask') 
def handleTask(task: Task) -> CompletedTask:
    result = 0
    match task.type:
        case 'generate_nth_fibonacci':
            result = generate_nth_fibonacci(task.n)
        case 'generate_n_factorial':
            result = generate_n_factorial(task.n)
        case _:
            logger.info(f'Encountered exception: 501 Not Implemented\n {task}')
            raise HTTPException(
                status_code=501, 
                detail='No method available to handle the task'
            )

    completed_task = CompletedTask(
        result = result
    )
    global numOfCompletedTasks 
    numOfCompletedTasks += 1
    logger.info(f'Successfully handled the task\n {task}')
    return completed_task