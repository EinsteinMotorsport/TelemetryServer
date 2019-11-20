class SendingClass():
    """
    Class for sending configuration to the car

    To reduce data transmission not all telemetry variables are transmitted
    from the car to the server. The configuration can be done with this class.
    """
    def __init__(self, car_connection):
        """
        Args:
            car_connection: CarConnection object for data transmission
        """

        self._configuration = [
            [False, False, False, False, False, False, False, False],
            [False, False, False, False, False, False, False, False],
            [False, False, False, False, False, False, False, False],
            [False, False, False, False, False, False, False, False]
        ]

        self._car_connection = car_connection

    def set_configuration(self, data):
        """Funktion um die Konfiguration zu ueberpruefen und zu laden"""
        """
        Set configuration

        Check if configuration has the correct format and then set it in
        preparation for transmission.

        The correct format is: A list of 4 lists each containing 8 booleans.
        Each boolean represents a CAN ID inside the car. If the boolean is true
        all data of this CAN ID is sent to the server. The first boolean
        represents the lowest CAN ID.

        Args:
            data: new configuration

        Raises:
            ValueError: If the passed configuration does not have the correct
                format
        """

        ok = True
        if len(data) != 4:
            ok = False
        else:
            for i in data:
                if len(i) != 8:
                    ok = False

        if ok:
            print('configuration ok')
            self._configuration = data
            # self.send_message()
        else:
            raise ValueError("Incorrect configuration")

    def _build_configuration_message(self):
        """
        Convert configuration transmittable package

        To transmit the configuration it must be converted into a data package
        that can be sent to the car.
        """

        start_signal = '02'
        command = '00'
        length = '05'
        uart_signal = 'DD'
        message = ''
        payload = ['', '', '', '']
        for num, byte in enumerate(self._configuration):
            for bit in byte:
                if bit:
                    payload[num] += '1'
                else:
                    payload[num] += '0'

        for i, j in enumerate(payload):
            b = str(hex(int(j[::-1], 2))).replace('0x', '')

            # Checks if the payload has an odd size and adds an leading zero
            if len(b) % 2 != 0:
                b = '0' + b
            payload[i] = b

        message += start_signal
        message += command
        message += length
        message += uart_signal
        message += ''.join(payload)
        c = 0
        checksum = 0

        # going through the bytes of the string with a XOR
        while c < len(message):
            checksum ^= int(message[c] + message[c + 1], 16)
            c += 2
        message += '{0:02X}'.format(checksum)
        print(message)
        return message

    def send_message(self):
        """
        Send configuration message to car
        """

        data_to_send = self._build_configuration_message()
        self._car_connection.send(data_to_send)
