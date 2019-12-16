from importlib import resources

import toml


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

        raise DeprecationWarning

        self._configuration = [
            [False, False, False, False, False, False, False, False],
            [False, False, False, False, False, False, False, False],
            [False, False, False, False, False, False, False, False],
            [False, False, False, False, False, False, False, False]
        ]

        self._car_connection = car_connection

    def set_configuration(self, data):
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

        raise DeprecationWarning

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

        raise DeprecationWarning

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

        raise DeprecationWarning

        data_to_send = self._build_configuration_message()
        self._car_connection.send(data_to_send)


class ConfigurationHandler:
    """
    Handler class for complete configuration regarding telemetry variables.

    The complete configuration includes:
    ▸ Resolution of CanIDs - which CanID includes which telemetry variable.
    ▸ specific configuration for each telemetry variable:
        length, signed?, offset, factor
    ▸ configuration to determine which CanIDs the car is should transmit.

    The first two are directly accessible through this class, the last one
    if dynamically generated if necessary. The access to the configuration is
    possible with the [] operator. Both CanIDs (e.g. '0x10') and telemetry
    variables (e.g. 'tmot') can be accessed directly, even though the data is
    separated internally.
    """
    def __init__(self, configuration_data):
        self._conf = configuration_data

    def __getitem__(self, key):
        if isinstance(key, int):
            key = hex(key)

        if key in self._conf["telemetry_var"]:
            return self._conf["telemetry_var"][key]

        elif key in self._conf["can_id"]:
            return self._conf["can_id"][key]

        raise KeyError

    @property
    def can_ids(self):
        return sorted(self._conf["can_id"].keys())

    def build_configuration_package(self,
                                    requested_variables,
                                    *,
                                    lowest_can_id=0x10):
        """
        Return configuration that can be transmitted to the car.

        Build configuration package, so the car will send only variables
        passed in the requested variables parameter.

        Args:
            requested_variables (list): list of all variables that are
                requested by the server.

        Keyword Args:
            lowest_can_id (int): the lowest CanID configured in the motor
                controller, all the other CanIDs are consecutive numbers.
                Defaults to 0x10
        """
        config_bytes = [0, 0, 0, 0]

        for req_var in requested_variables:

            # if a requested variable is not a CanID it must be resolved
            # to the correct CanID
            if req_var in self._conf["telemetry_var"]:
                for can_id in self.can_ids:
                    if req_var in self[can_id]:
                        req_var = can_id

            req_var = int(req_var) - lowest_can_id

            # set the correct bit inside the config bytes
            config_bytes[req_var // 8] += 2**(req_var % 8)

        # add the 4 config bytes together consecutively in hex format
        finished_config = "".join([f"{byte:0>8x}" for byte in config_bytes])

        return self._build_package(finished_config)

    @staticmethod
    def _build_package(payload):
        start_signal = '02'
        command = '00'
        length = '05'
        uart_signal = 'DD'

        package = start_signal + command + length + uart_signal + payload

        checksum = 0

        for byte_index in range(0, len(package), 2):
            checksum ^= int(package[byte_index:byte_index + 2], 16)

        package += f"{checksum:0>8x}"

        return package


def get_configuration() -> ConfigurationHandler:
    """
    Return object containing telemetry configuration

    Load configuration file from disk and create a ConfigurationHandler object
    with it.

    The configuration language TOML is used for the config file.
    See: https://github.com/toml-lang/toml

    Returns:
        ConfigurationHandler: Object which contains telemetry configuration
    """

    with resources.open_text("telemetryserver.res",
                             "telemetry_config.toml") as conf_file:
        conf_data = toml.load(conf_file)

    return ConfigurationHandler(conf_data)
