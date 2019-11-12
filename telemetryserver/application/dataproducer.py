import json

from telemetryserver.data.processing import DataProcessing
from telemetryserver.transmission import CarConnection


def communication(com_port_identifier, pipe_connection):
    car_connection = CarConnection(com_port_identifier)
    data_processing = DataProcessing()
    while True:
        received_package = car_connection.receive()

        processed_data = data_processing.process_data(received_package)
        messages = [json.dumps(data) for data in processed_data]

        for msg in messages:
            pipe_connection.send(msg)

        if pipe_connection.poll():
            # dummy statement for future uses when bidirectional communication
            # is necessary
            pass
