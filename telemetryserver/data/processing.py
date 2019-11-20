import datetime
import threading
import time
from importlib import resources

import numpy

LOOK_UP_FILE_NAME = 'Daten_verarbeiten_konfig_AL19.txt'
CONFIG_FILE_NAME = 'Daten_aufbereiten_konfig_AL19.txt'


class DataProcessing:
    """
    Process incoming data from car
    """
    def __init__(self):

        # hier werden die Zusammenstellungen der grossen ID's gespeichert
        # [ID] : [([Laenge, id), ...]
        self.look_up_dict = self._load_lookup_table(LOOK_UP_FILE_NAME)
        # [id] : [signed/unsigned], [Factor], [Offset]
        self.id_name_dict, self.conf_dict = self._load_config_table(
            CONFIG_FILE_NAME)

        self.indexErrorCounter = 0
        self.wrong_id_counter = 0

        # speichert Anzahl Auftreten von grossen IDs
        self.id_counter_dict = {}

        self.start_time = datetime.datetime.now().strftime(
            "%Y_%m_%d__%H_%M_%S")

        # self.start_id_counter_thread()

    def process_data(self, value):
        """
        Process incoming packages from car

        If length of package is correct, process the package and return a list
        of messages that can be sent via websocket.

        Args:
            package: package data received from the car

        Returns:
            list: list of all telemetry variables and their values in form of
                messages that can be sent to the telemetry clients
        """

        # ueberprueft ob die Laenge des Packets passt
        if len(value) == 134:
            return self.lookup_position_and_ids_of_bytes_decimal_server(value)
        else:
            # print('wrong package length')
            return []

    @staticmethod
    def _load_lookup_table(file_name: str):
        """
        Load id lookup file

        Args:
            file_name: Name of file located in res subpackage

        Returns:
            dict: look_up_dict
        """

        look_up_dict = dict()

        with resources.open_text("telemetryserver.res", file_name) as table:
            for line in table:
                tmp = line.strip().split('~')
                look_up_dict[tmp[0]] = []
                for k in range(1, len(tmp), 2):
                    look_up_dict[tmp[0]].append((tmp[k], tmp[k + 1]))

        return look_up_dict

    @staticmethod
    def _load_config_table(file_name: str):
        """
        Load config file

        Args:
            file_name: Name of config file located in res subpackage

        Returns:
            Tuple[dict, dict]: id_name_dict, conf_dict
        """

        id_name_dict = dict()
        conf_dict = dict()

        with resources.open_text("telemetryserver.res", file_name) as conf:
            for line in conf:
                tmp = line.strip().split('~')
                id_name_dict[tmp[0]] = tmp[1]
                tmp1 = tmp[2].split(' ')
                conf_dict[tmp[0]] = ((tmp1[0], tmp1[2]), float(tmp[3]),
                                     float(tmp[4]))
        return id_name_dict, conf_dict

    def store_id_counter_dict(self):
        """speichert id_counter_dict in eine Txt-Datei"""
        # create_time = datetime.datetime.now().strftime("%Y_%m_%d__%H_%M_%S")
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

        store_counter_thread = threading.Thread(
            target=self.store_id_counter_dict, )
        store_counter_thread.start()

    def _convert_unsigned_to_signed(self, number):
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

        Returns:
            correct value according to conf_dict
        """

        # FIXME? Why is number used to look up the config AND then number is
        #        converted?
        if self.conf_dict[number][0][0] == '8':
            number = numpy.int8(number)
        elif self.conf_dict[number][0][0] == '16':
            number = numpy.int16(number)
        elif self.conf_dict[number][0][0] == '32':
            number = numpy.int32(number)
        return int(number)

    @staticmethod
    def _convert_bytes_to_hex(*args):
        """konvertiert integer Werte in Hex-Werte und setzt sie zusammen"""

        hex_value = ''
        for j, i in enumerate(args):
            tmp_hex = str(hex(i)).replace('0x', '')
            if len(tmp_hex) == 1:
                tmp_hex = '0' + tmp_hex
            hex_value += tmp_hex
        return hex_value

    def _convert_bytes_to_decimal(self, id, *args):
        """
        konvertiert integer Werte in Hex-Werte, setzt sie zusammen
        und gibt diese dezimal als integer zurueck
        """

        hex_value = ''
        for j, i in enumerate(args):
            tmp_hex = str(hex(i)).replace('0x', '')
            if len(tmp_hex) == 1:
                tmp_hex = '0' + tmp_hex
            hex_value = tmp_hex + hex_value

        tmp_int = int(hex_value, 16)
        if self.conf_dict[id][0][1] == 'signed':
            # FIXME? Why is id converted from unsigned to signed
            #   and not temp_int?
            tmp_int = self._convert_unsigned_to_signed(id)
        return tmp_int * self.conf_dict[id][1] + self.conf_dict[id][2]

    def _get_payload_and_signal_strength(self, received_data):
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

    def lookup_position_and_ids_of_bytes_decimal_server(self, data):
        """iteriert durch empfangenes Daten-Paket und separiert IDs und Nutzdaten
         -> schickt jede id mit Wert direkt an den Webserver"""

        n_data, strength = (self._get_payload_and_signal_strength(data))

        # print('strength: ', strength)
        counter = 0
        messages = []
        # temp = {}
        while counter < len(n_data):
            big_id = self._convert_bytes_to_hex(n_data[counter])
            counter += 1
            if big_id in self.id_counter_dict:
                self.id_counter_dict[big_id] += 1
            else:
                self.id_counter_dict[big_id] = 1
            try:
                pos_list = self.look_up_dict[big_id]
            except KeyError:
                if big_id == '0':
                    break
                else:
                    print('Wrong ID: ', big_id)
                    counter += 8
                    self.wrong_id_counter += 1
                    continue
            for var in pos_list:
                tmp = []
                try:
                    for b in range(counter, counter + int(int(var[0]) / 8)):
                        tmp.append(n_data[b])

                except IndexError:
                    self.indexErrorCounter += 1
                    break

                messages.append([
                    int(var[1]),
                    self._convert_bytes_to_decimal(var[1], *tmp)
                ])

                # temp[var[1]] = self._convert_bytes_to_decimal(
                # var[1], *tmp)
                counter += int(int(var[0]) / 8)

        return messages
