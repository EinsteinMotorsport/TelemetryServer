import aioprocessing
from serial.tools import list_ports
from telemetryserver.application import dataproducer, websocket

if __name__ == "__main__":
    port_identifier = None
    for port in list_ports.comports():
        # Check for VendorID and ProductID in hardware id of antenna
        if "0403:6001" in port.hwid:
            # port identifier is first part of str(port) (until whitespace)
            port_identifier = str(port).split()[0]
            print(f"Portnumber: {port_identifier}")

    if port_identifier is None:
        raise IOError("Antenna is not connected!")

    left_pipe_end, right_pipe_end = aioprocessing.Pipe()

    # Instanz von parallelen Prozess mit Webserver wird erstellt
    p = aioprocessing.Process(target=dataproducer.communication,
                              args=(port_identifier, left_pipe_end))

    # Prozess wird gestartet
    p.start()

    websocket.start_server(right_pipe_end)
