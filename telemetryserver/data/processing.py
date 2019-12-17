import datetime
import threading
import time
from typing import Sequence

import numpy


def process_data(package, config):
    """
    Process incoming packages from car

    If length of package is correct, process the package and return a list
    of messages that can be sent via websocket.

    Args:
        package: package data received from the car
        config (ConfigHandler): Instance of ConfigHandler that contains the
            current config.

    Returns:
        list: list of all telemetry variables and their values in form of
            messages that can be sent to the telemetry clients
    """

    if len(package) == 134:
        return generate_messages(package, config)

    return []


def store_id_counter_dict(self):
    """speichert id_counter_dict in eine Txt-Datei"""
    # create_time = datetime.datetime.now().strftime("%Y_%m_%d__%H_%M_%S")
    # TODO refactor

    raise DeprecationWarning

    while True:
        try:
            with open('id_counter_dict__' + self.start_time + '.txt',
                      'a') as counter_file:
                print(datetime.datetime.now().strftime("%H_%M_%S"),
                      '\t',
                      self.id_counter_dict,
                      file=counter_file)
                time.sleep(5)

        except FileNotFoundError:
            with open('id_counter_dict__' + self.start_time + '.txt',
                      'w') as o:
                print("Auftritte der einzelnen ID's:", file=o)


def start_id_counter_thread(self):
    """
    startet Thread, welcher das id_counter_dict
    alle fuenf Sekunden in eine Datei schreibt
    """
    # TODO refactor
    raise DeprecationWarning

    store_counter_thread = threading.Thread(
        target=self.store_id_counter_dict, )
    store_counter_thread.start()


def _convert_unsigned_to_signed(number: int, bitlength: int) -> int:
    """
    Convert unsigned number to signed number

    Conversion from hex into int does not take the length of the number
    into account. So if an 8 bit signed number is converted from hex to
    int with python builtins, the number is not interpreted as an 8 bit
    number, which leads to false values if the number is negative.

    Therefore the number needs to be converted to the correct value. This
    is done using numpy.

    Args:
        number: Input number, which might have wrong value
        bitlength: length of number in bits

    Returns:
        correct value according to conf_dict
    """

    if bitlength == 8:
        number = numpy.int8(number)
    elif bitlength == 16:
        number = numpy.int16(number)
    elif bitlength == 32:
        number = numpy.int32(number)
    else:
        raise ValueError("bitlength needs to be 8, 16 or 32")

    return int(number)


def _bytelist_to_integer(byte_list: Sequence,
                         *,
                         little_endian: bool = True) -> int:
    """
    Convert a list of bytes to an integer.

    Args:
        byte_list: A sequence of bytes which will be converted

    Keyword Args:
        little_endian: If True, byte_list is in little endian format, else
            in big endian format. Defaults to True.

    Returns:
        int: correct integer
    """

    if not little_endian:
        byte_list = tuple(reversed(byte_list))

    result = 0
    for n, byte in enumerate(byte_list):
        result += byte * (256**n)

    return result


def _apply_configuration_to_variable(var_config: dict,
                                     byte_list: Sequence) -> int:
    """
    Convert a list of bytes to the correct integer value.

    First convert the content of the bytelist to a hexadecimal string.
    Then convert this string into an integer, and converting this integer
    into the correct form by taking (un)signed into account.
    Compute the correct value for the telemetry_var by multiplying with a
    certain factor and adding an offset.

    Args:
        var_config: dictionary containing configuration for the telemetry
            variable that needs to be converted
        byte_list: sequence of of the bytes in little endian format

    Returns:
        int: correctly converted and computed value of the bytelist
    """

    int_value = _bytelist_to_integer(byte_list, little_endian=True)

    if var_config["signed"]:
        int_value = _convert_unsigned_to_signed(int_value, var_config["size"])

    return int_value * var_config["factor"] + var_config["offset"]


def _get_payload_and_signal_strength(received_data):
    """
    Separate payload and non payload bytes and get signal strength

    Args:
        received_data: whole package received from the car

    Returns:
        Tuple[list, byte]: List of payload bytes, signal strength
    """

    signal_strength = received_data[-2]
    new_list = received_data[4:-2]
    return new_list, signal_strength


def generate_messages(data, config):
    """
    Parse package and generate messages with telemetry data

    Parse the received package according to the configuration and generate a
    list of messages with the processed values.

    Args:
        data (list): List of bytes from the data package
        config (ConfigHandler): Instance of ConfigHandler which contains the
            current config.

    Returns:
        list: List of messages. Each message contains the id of the variable
            and the processed value.
    """

    payload_data, signal_strength = _get_payload_and_signal_strength(data)

    counter: int = 0
    messages: list = []

    while counter < len(payload_data):
        can_id: str = hex(payload_data[counter])
        counter += 1

        # if can_id in self.id_counter_dict:
        # self.id_counter_dict[can_id] += 1
        # else:
        # self.id_counter_dict[can_id] = 1

        try:
            telemetry_vars: list = config["can_id"][can_id]
        except KeyError:
            if can_id == '0x0':
                break
            else:
                print('Wrong ID: ', can_id)
                counter += 8
                # self.wrong_id_counter += 1
                continue

        for variable in telemetry_vars:
            var_config = config["telemetry_var"][variable]
            size = var_config["size"]

            var_data = payload_data[counter:counter + size // 8]

            if len(var_data) != size // 8:
                print("Index Error")
                break

            messages.append([
                var_config["id"],
                _apply_configuration_to_variable(var_config, var_data)
            ])

            counter += size // 8

    return messages
