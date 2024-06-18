import requests
import asyncio
import aiohttp

from utils import HOST, BASE_PORT
from random import randint
from time import time


async def send_test_requests(num_of_requests: int) -> None:
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
                f'http://{HOST}:{BASE_PORT}/api/private/sendTask', json=task
            ) for _ in range(num_of_requests)
        ]
        responses = await asyncio.gather(*tasks)
        print('Responses:')
        for response in responses:
            print(response)

    end = time()
    
    print('Server info:')  
    info = requests.get(f'http://{HOST}:{BASE_PORT}/api/public/getInfo').json()
    print(info)
    print('Time taken:', round(end-start, 2))


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    loop.run_until_complete(send_test_requests(20))
