import json
import pickle
import time
from importlib.resources import open_binary

import aioprocessing

from telemetryserver.application import websocket
from telemetryserver.data import configuration
from telemetryserver.data.processing import process_data


def parse_test_data(pipe_connection):
    with open_binary("telemetryserver.tests", "testdata.p") as f:
        test_data = pickle.load(f)

    config = configuration.get_configuration()

    for received_package in test_data:
        time.sleep(0.01)
        processed_data = process_data(received_package, config)

        for msg in processed_data:
            pipe_connection.send(json.dumps(msg))

        if pipe_connection.poll():
            pass


def run_test():
    left_pipe_end, right_pipe_end = aioprocessing.AioPipe()

    p = aioprocessing.AioProcess(target=parse_test_data,
                                 args=(left_pipe_end, ))

    p.start()

    websocket.start_server(right_pipe_end)
