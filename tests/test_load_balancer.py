import uvicorn
import requests
import asyncio
import aiohttp

from multiprocessing import Process
from time import sleep
from ..src.config import (
    Settings
)


ServerSettings = Settings()
load_balancer_app_name = 'loadBalancer.src.load_balancer.load_balancer:load_balancer'
server_app_name = 'loadBalancer.src.server.resources:server'


async def send_test_requests(num_of_requests: int) -> None:
    n = 300000
    task = {
        "type": "generate_nth_fibonacci",
        "n": n
    }
    
    async with aiohttp.ClientSession() as session:
        tasks = [
            session.post(
                f'http://{ServerSettings.HOST}:{ServerSettings.BASE_PORT}/api/private/sendTask', json=task
            ) for _ in range(num_of_requests)
        ]
        responses = await asyncio.gather(*tasks)
        print('Responses:')
        for response in responses:
            print(response)

    print('Server info:')  
    info = requests.get(f'http://{ServerSettings.HOST}:{ServerSettings.BASE_PORT}/api/public/getInfo').json()
    print(info)


def prepare_load_balancer_process():
    return Process(target=uvicorn.run, kwargs={
        'app': load_balancer_app_name, 
        'port': ServerSettings.BASE_PORT
    })


def test_load_balancer():
    port = ServerSettings.BASE_PORT + 1
    proc = prepare_load_balancer_process()
    proc.start()
    total_time_slept = 0
    while not proc.is_alive() and time_slept < ServerSettings.PROCESS_CREATION_TIMEOUT_SEC:
        time_slept = 0.05
        sleep(time_slept)
        total_time_slept += time_slept
    if(total_time_slept > 2):
        raise Exception('Could not start the server process')

    request = requests.get(f'http://{ServerSettings.HOST}:{ServerSettings.BASE_PORT}/api/public/getInfo').json()
    assert request['numOfServers'] == 0
    assert request['numOfCompletedTasks'] == []

    data = {'type': server_app_name, 'n': 3}
    request = requests.post(f'http://{ServerSettings.HOST}:{ServerSettings.BASE_PORT}/api/private/addNewCopy', json=data).json()
    assert request['status'] == 'success'
    assert request['detail'] == 'Successfully added 3 server copies'

    request = requests.get(f'http://{ServerSettings.HOST}:{ServerSettings.BASE_PORT}/api/public/getInfo').json()
    assert request['numOfServers'] == 3
    assert request['numOfCompletedTasks'] == [
        ['Server #1', 0], 
        ['Server #2', 0], 
        ['Server #3', 0]
    ]

    request = requests.post(f'http://{ServerSettings.HOST}:{ServerSettings.BASE_PORT}/api/private/deleteCopy', json=data).json()
    assert request['status'] == 'success'
    assert request['detail'] == 'Successfully deleted 3 server copies'

    request = requests.get(f'http://{ServerSettings.HOST}:{ServerSettings.BASE_PORT}/api/public/getInfo').json()
    assert request['numOfServers'] == 0
    assert request['numOfCompletedTasks'] == []


    requests.post(f'http://{ServerSettings.HOST}:{ServerSettings.BASE_PORT}/api/private/addNewCopy', json=data)

    task = {
        "type": "generate_nth_fibonacci",
        "n": 10
    }
    request = requests.post(f'http://{ServerSettings.HOST}:{ServerSettings.BASE_PORT}/api/private/sendTask', json=task).json()
    assert request['result'] == 34

    request = requests.get(f'http://{ServerSettings.HOST}:{ServerSettings.BASE_PORT}/api/public/getInfo').json()
    assert request['numOfServers'] == 3
    assert request['numOfCompletedTasks'] == [
        ['Server #1', 1], 
        ['Server #2', 0], 
        ['Server #3', 0]
    ]

    loop = asyncio.new_event_loop()
    loop.run_until_complete(send_test_requests(5))

    request = requests.get(f'http://{ServerSettings.HOST}:{ServerSettings.BASE_PORT}/api/public/getInfo').json()
    assert request['numOfServers'] == 3
    assert request['numOfCompletedTasks'] == [
        ['Server #1', 2], 
        ['Server #2', 2], 
        ['Server #3', 2]
    ]

    request = requests.post(f'http://{ServerSettings.HOST}:{ServerSettings.BASE_PORT}/api/private/deleteCopy', json=data).json()
    assert request['status'] == 'success'
    assert request['detail'] == 'Successfully deleted 3 server copies'

    request = requests.get(f'http://{ServerSettings.HOST}:{ServerSettings.BASE_PORT}/api/public/getInfo').json()
    assert request['numOfServers'] == 0
    assert request['numOfCompletedTasks'] == []

    proc.kill()
