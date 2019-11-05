import serial

from . import AMB8826


class CarConnection:
    """
    Serial communication wrapper for remote connection to car

    This class wraps the serial port communication to the antenna, so
    that bidirectional communication is made easier.
    """
    def __init__(self, com_port: str):
        """
        Set up serial communication

        Initialize serial communication to antenna, which transmits data
        to and receives data from the car.

        Args:
            com_port: name of serial com port of antenna
        """

        self._serial_connection = serial.Serial(port=com_port,
                                                baudrate=115200,
                                                parity=serial.PARITY_NONE,
                                                stopbits=serial.STOPBITS_ONE,
                                                bytesize=serial.EIGHTBITS)

    def send(self, data: str):
        """
        Send data to car

        Args:
            data: data to send to car
        """

        AMB8826.send_data(self._serial_connection, data)

    def receive(self):
        """
        Receive a data package from the car

        Returns:
            Data package
        """

        return AMB8826.get_answer_address_mode_1(self._serial_connection)
