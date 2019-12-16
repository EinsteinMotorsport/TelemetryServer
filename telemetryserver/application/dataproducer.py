import json

from telemetryserver.data import configuration
from telemetryserver.data.processing import process_data
from telemetryserver.transmission import CarConnection


def communication(com_port_identifier, pipe_connection):
    car_connection = CarConnection(com_port_identifier)
    config = configuration.get_configuration()
    while True:
        received_package = car_connection.receive()

        processed_data = process_data(received_package, config)
        # TODO id counter

        for msg in processed_data:
            pipe_connection.send(json.dumps(msg))

        if pipe_connection.poll():
            # dummy statement for future uses when bidirectional communication
            # is necessary
            pass
