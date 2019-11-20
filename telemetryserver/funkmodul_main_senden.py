from serial.tools import list_ports
from telemetryserver.data import configuration
from telemetryserver.transmission import CarConnection

if __name__ == '__main__':
    # Automatically find the correct com port of the antenna
    port_identifier = None
    for port in list_ports.comports():
        # Check for VendorID and ProductID in hardware id of antenna
        if "0403:6001" in port.hwid:
            # port identifier is first part of str(port) (until whitespace)
            port_identifier = str(port).split()[0]
            print(f"Portnumber: {port_identifier}")

    car_connection = CarConnection(port_identifier)
    sending_protocol = configuration.SendingClass(car_connection)

    # 8 bytes of configuration representing CAN IDs in ascending order
    config = [[True, False, False, False, False, False, False, False],
              [False, False, False, False, False, False, False, False],
              [False, False, False, False, False, False, False, False],
              [False, False, False, False, False, False, False, False]]

    # set and send configuration
    sending_protocol.set_configuration(config)
    sending_protocol.send_message()
