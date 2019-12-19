from itertools import islice
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
    payload = received_data[4:-2]
    return payload, signal_strength


def _payload_iterator(payload):
    """
    Iterate over the payload of a package

    Iterator that iterates over a package by separating it into can messages.

    Yields:
        tuple: For each can message yields a tuple of length 2 that contains
            a hex string of the can_id and an iterator of the bytes of the
            can message.
    """

    payload_iter = iter(payload)

    while True:
        can_id, *can_message = tuple(islice(payload_iter, 9))

        if len(can_message) != 8:
            break

        yield hex(can_id), iter(can_message)


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

    messages: list = []

    for can_id, can_message in _payload_iterator(payload_data):
        if can_id in config.can_ids:
            telemetry_vars = config[can_id]
        elif can_id == '0x0':
            break
        else:
            print(f"Wrong ID: {can_id}")

        for tel_var in telemetry_vars:
            var_config = config[tel_var]
            size = var_config["size"]

            var_data = list(islice(can_message, size // 8))

            if len(var_data) != size // 8:
                print("Error wrong tel_var size!")

            messages.append([
                var_config["id"],
                _apply_configuration_to_variable(var_config, var_data)
            ])

    return messages
