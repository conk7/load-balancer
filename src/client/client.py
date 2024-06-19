import requests
import asyncio
import aiohttp
import logging

from ..config import (
    Settings
)
from random import randint
from time import time


logger = logging.getLogger('client')
ClientSettings = Settings()


async def send_test_requests(num_of_requests: int) -> None:

    logging.basicConfig(filename='./src/client/client.log', level=logging.INFO)
    logger.info('Started')

    # n = randint(300000,300001)
    n = 300000
    task = {
        "type": "generate_nth_fibonacci",
        "n": n
    }
    start = time()

    async with aiohttp.ClientSession() as session:
        tasks = [
            session.post(
                f'http://{ClientSettings.HOST}:{ClientSettings.BASE_PORT}/api/private/sendTask', json=task
            ) for _ in range(num_of_requests)
        ]
        responses = await asyncio.gather(*tasks)
        logger.info('Responses:')
        for response in responses:
            logger.info(response)

    end = time()
    
    logger.info('Server info:')  
    info = requests.get(f'http://{ClientSettings.HOST}:{ClientSettings.BASE_PORT}/api/public/getInfo').json()
    logger.info(info)
    tame_taken = round(end-start, 2)
    logger.info(f'Time taken: {tame_taken}')

    logger.info('Finished\n')


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    loop.run_until_complete(send_test_requests(20))
