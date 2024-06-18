import pytest
import uvicorn
import requests

from multiprocessing import Process
from time import sleep
from ..src.server import (
    generate_n_factorial, 
    generate_nth_fibonacci
)
from ..src.utils import (
    BASE_PORT,
    HOST,
    PROCESS_CREATION_TIMEOUT_SEC
)


@pytest.mark.parametrize(
    ('n', 'result'), [
        (10, 3628800),
        (1, 1),
        (0, 1),
        (-1,-1)
    ]
)
def test_generate_n_factorial(n, result):
    assert generate_n_factorial(n) == result


@pytest.mark.parametrize(
    ('n', 'result'), [
        (0, -1),
        (10, 34),
        (3, 1),
    ]
)
def test_generate_nth_fibonacci(n, result):
    assert generate_nth_fibonacci(n) == result


def prepare_server_process(port: int):
    return Process(target=uvicorn.run, kwargs={'app': 'loadBalancer.src.server:server', 'port': port})

def test_server():
    port = BASE_PORT + 100
    proc = prepare_server_process(port)
    proc.start()
    total_time_slept = 0
    while not proc.is_alive() and time_slept < PROCESS_CREATION_TIMEOUT_SEC:
        time_slept = 0.05
        sleep(time_slept)
        total_time_slept += time_slept
    if(total_time_slept > 2):
        raise Exception('Could not start the server process')

    request = requests.get(f'http://{HOST}:{port}/api/getInfoInternal').json()

    assert request['numOfCompletedTasks'] == 0
    assert request['pid'] == proc.pid

    task = {
        "type": "generate_nth_fibonacci",
        "n": 10
    }
    request = requests.post(f'http://{HOST}:{port}/api/sendTask', json=task).json()

    assert len(request) == 1
    assert request['result'] == 34

    task = {
        "type": "generate_n_factorial",
        "n": 5
    }
    request = requests.post(f'http://{HOST}:{port}/api/sendTask', json=task).json()

    assert len(request) == 1
    assert request['result'] == 120

    proc.kill()
