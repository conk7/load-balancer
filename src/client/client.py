import requests
import asyncio
import aiohttp
import logging
import time
from pydantic_core import ValidationError
from ..config import Settings
from ..utils import ServerCopyResponse


logger = logging.getLogger('client')
ClientSettings = Settings()


async def send_test_requests(num_of_requests: int) -> None:

    logging.basicConfig(filename='./src/client/client.log', level=logging.INFO)
    logger.info('Started')

    serverCopiesInfo = {"type": "src.server.resources:server","n": 2}
    info = requests.post(f'http://{ClientSettings.HOST}:{ClientSettings.BASE_PORT}/api/private/addNewCopy', json=serverCopiesInfo).json()

    try:
        info = ServerCopyResponse.model_validate(info)
    except ValidationError:
        logger.info('Received invalid data')
        return
    
    if info.status != 'success':
        logger.info('Load balancer could not create server copies.')
        return

    n = 300000
    task = {
        "type": "generate_nth_fibonacci",
        "n": n
    }
    start = time.monotonic()

    async with aiohttp.ClientSession() as session:
        tasks = [
            session.post(
                f'http://{ClientSettings.HOST}:{ClientSettings.BASE_PORT}/api/private/sendTask', json=task
            ) for _ in range(num_of_requests)
        ]
        await asyncio.gather(*tasks)

    end = time.monotonic()
    logger.info(f'Successfully sent {num_of_requests} requests')
    logger.info('Server info:')  

    info = requests.get(f'http://{ClientSettings.HOST}:{ClientSettings.BASE_PORT}/api/public/getInfo').json()

    num_of_active_servers = info['numOfServers']
    num_of_tasks_per_server = info['numOfCompletedTasks']
    logger.info(f'Number of active servers {num_of_active_servers}')
    for server in num_of_tasks_per_server:
        logger.info(f'{server[0]} successfully handled {server[1]} tasks')

    time_taken = round(end-start, 2)

    info = requests.post(f'http://{ClientSettings.HOST}:{ClientSettings.BASE_PORT}/api/private/deleteCopy', json=serverCopiesInfo).json()
    try:
        info = ServerCopyResponse.model_validate(info)
    except ValidationError:
        logger.info('Received invalid data')
        return
    
    if info.status != 'success':
        logger.info('Load balancer could not delete server copies.')
        return

    logger.info(f'Time taken to handle responses: {time_taken}')
    logger.info('Successfully finished\n')


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    loop.run_until_complete(send_test_requests(20))
