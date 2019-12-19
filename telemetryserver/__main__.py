import sys

import aioprocessing
from serial.tools import list_ports

from telemetryserver.application import dataproducer, websocket


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "server_test":
            from telemetryserver.tests import server_test
            server_test.run_test()

    else:
        port_identifier = None
        for port in list_ports.comports():
            # Check for VendorID and ProductID in hardware id of antenna
            if "0403:6001" in port.hwid:
                # port identifier is first part of str(port) (until whitespace)
                port_identifier = str(port).split()[0]
                print(f"Portnumber: {port_identifier}")

        if port_identifier is None:
            raise IOError("Antenna is not connected!")

        left_pipe_end, right_pipe_end = aioprocessing.AioPipe()

        # separate process that contains communication and data processing
        # pass one end of the pipe so data can be sent to this process
        p = aioprocessing.AioProcess(target=dataproducer.communication,
                                     args=(port_identifier, left_pipe_end))

        p.start()

        # pass other end of the pipe to the websocket server, to receive
        # telemetry from the other process
        websocket.start_server(right_pipe_end)


if __name__ == "__main__":
    main()
