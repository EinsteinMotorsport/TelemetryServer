import datetime
import threading
import time

import numpy


class ReceiveProtocol:
    """Klasse zum Verarbeiten der empfangenen Daten"""

    instance_counter = 0
    look_up_table_path = 'Daten_verarbeiten_konfig_AL19.txt'
    config_table_path = 'Daten_aufbereiten_konfig_AL19.txt'

    def __init__(self, queue=None):

        # hier werden die Zusammenstellungen der grossen ID's gespeichert
        # [ID] : [([Laenge, id), ...]
        self.look_up_dict = {}
        # [id] : [signed/unsigned], [Factor], [Offset]
        self.conf_dict = {}
        self.id_name_dict = {}

        self.indexErrorCounter = 0
        self.wrong_id_counter = 0

        # speichert Anzahl Auftreten von grossen IDs
        self.id_counter_dict = {}

        self.load_lookup_table_from_file()
        self.load_config_table_from_file()

        self.start_time = datetime.datetime.now().strftime(
            "%Y_%m_%d__%H_%M_%S")

        type(self).instance_counter += 1

        self.que = queue

        # self.start_id_counter_thread()

    def __del__(self):
        type(self).instance_counter -= 1

    def setincoming_data(self, value):
        """Eingangsdaten setzten"""

        # ueberprueft ob die Laenge des Packets passt
        if len(value) == 134:
            self.lookup_position_and_ids_of_bytes_decimal_server(value)
        else:
            # print('wrong package length')
            pass

    # .txt - File ( ID,Pos1,Var1, Pos2, Var2...)
    def load_lookup_table_from_file(self):
        """laed die Konfiguratons-Datei der ID's in ein Dictionary"""

        with open(type(self).look_up_table_path, 'r') as table:
            for line in table:
                tmp = line.strip().split('~')
                self.look_up_dict[tmp[0]] = []
                for k in range(1, len(tmp), 2):
                    self.look_up_dict[tmp[0]].append((tmp[k], tmp[k + 1]))

    def load_config_table_from_file(self):
        """
        laed die Konfigurations_Datei der Faktoren,
        Namen und Einheiten der ID's in Dictionaries
        """

        with open(type(self).config_table_path, 'r') as conf:
            for line in conf:
                tmp = line.strip().split('~')
                self.id_name_dict[tmp[0]] = tmp[1]
                tmp1 = tmp[2].split(' ')
                self.conf_dict[tmp[0]] = ((tmp1[0], tmp1[2]), float(tmp[3]),
                                          float(tmp[4]))

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

    def convert_unsigned_to_signed(self, number):
        """konvertiert, falls noetig, die Werte von unsigned to signed"""

        if self.conf_dict[number][0][0] == '8':
            number = numpy.int8(number)
        elif self.conf_dict[number][0][0] == '16':
            number = numpy.int16(number)
        elif self.conf_dict[number][0][0] == '32':
            number = numpy.int32(number)
        return int(number)

    def convert_bytes_to_value_hex(self, *args):
        """konvertiert integer Werte in Hex-Werte und setzt sie zusammen"""

        hex_value = ''
        for j, i in enumerate(args):
            tmp_hex = str(hex(i)).replace('0x', '')
            if len(tmp_hex) == 1 and j > 0:
                tmp_hex = '0' + tmp_hex
            hex_value += tmp_hex
        return hex_value

    def convert_bytes_to_value_decimal(self, id, *args):
        """
        konvertiert integer Werte in Hex-Werte, setzt sie zusammen
        und gibt diese dezimal als integer zurueck
        """

        hex_value = ''
        for j, i in enumerate(args):
            tmp_hex = str(hex(i)).replace('0x', '')
            if len(tmp_hex) == 1 and j > 0:
                tmp_hex = '0' + tmp_hex
            hex_value = tmp_hex + hex_value

        tmp_int = int(hex_value, 16)
        if self.conf_dict[id][0][1] == 'signed':
            tmp_int = self.convert_unsigned_to_signed(id)
        return tmp_int * self.conf_dict[id][1] + self.conf_dict[id][2]

    def discard_non_payload_bytes_return_signal_strength(self, received_data):
        """
        schneidet die ueberschuessigen Bytes ab und gibt diese Liste zurueck
        """

        signal_strength = received_data[-2]
        new_list = received_data[4:-2]
        return new_list, signal_strength

    def lookup_position_and_ids_of_bytes_decimal_server(self, data):
        """iteriert durch empfangenes Daten-Paket und separiert IDs und Nutzdaten
         -> schickt jede id mit Wert direkt an den Webserver"""

        n_data, strength = (
            self.discard_non_payload_bytes_return_signal_strength(data))

        # print('strength: ', strength)
        counter = 0
        # temp = {}
        while counter < len(n_data):
            big_id = self.convert_bytes_to_value_hex(n_data[counter])
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

                self.que.put({
                    0:
                    int(var[1]),
                    1:
                    self.convert_bytes_to_value_decimal(var[1], *tmp)
                })

                # temp[var[1]] = self.convert_bytes_to_value_decimal(
                # var[1], *tmp)
                counter += int(int(var[0]) / 8)