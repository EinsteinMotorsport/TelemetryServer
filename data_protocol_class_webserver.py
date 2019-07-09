import datetime
import threading
import time
import sys

import numpy

import AMB8826

import json

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket


class ReceiveProtocol:
    """Klasse zum Verarbeiten der empfangenen Daten"""
    instance_counter = 0
    look_up_table_path = 'Daten_verarbeiten_konfig_AL19.txt'
    config_table_path = 'Daten_aufbereiten_konfig_AL19.txt'

    def __init__(self, queue=None):

        self.look_up_dict = {}  # hier werden die Zusammenstellungen der grossen ID's gespeichert [ID] : [([Laenge, id), ...]
        self.conf_dict = {}  # [id] : [signed/unsigned], [Factor], [Offset]
        self.id_name_dict = {}

        self.indexErrorCounter = 0
        self.wrong_id_counter = 0

        self.id_counter_dict = {}  # speichert Anzahl Auftreten von grossen IDs

        self.load_lookup_table_from_file()
        self.load_config_table_from_file()

        self.start_time = datetime.datetime.now().strftime("%Y_%m_%d__%H_%M_%S")

        type(self).instance_counter += 1

        self.que = queue

        # self.start_id_counter_thread()

    def __del__(self):
        type(self).instance_counter -= 1

    def setincoming_data(self, value):
        """Eingangsdaten setzten"""
        if len(value) == 134:  # ueberprueft ob die Laenge des Packets passt
            self.lookup_position_and_ids_of_bytes_decimal_server(value)
        else:
            # print('wrong package length')
            pass

    def load_lookup_table_from_file(self):  # .txt - File ( ID,Pos1,Var1, Pos2, Var2...)
        """laed die Konfiguratons-Datei der ID's in ein Dictionary"""
        with open(type(self).look_up_table_path, 'r') as table:
            for line in table:
                tmp = line.strip().split('~')
                self.look_up_dict[tmp[0]] = []
                for k in range(1, len(tmp), 2):
                    self.look_up_dict[tmp[0]].append((tmp[k], tmp[k + 1]))

    def load_config_table_from_file(self):
        """laed die Konfigurations_Datei der Faktoren, Namen und Einheiten der ID's in Dictionaries"""
        with open(type(self).config_table_path, 'r') as conf:
            for line in conf:
                tmp = line.strip().split('~')
                self.id_name_dict[tmp[0]] = tmp[1]
                tmp1 = tmp[2].split(' ')
                self.conf_dict[tmp[0]] = ((tmp1[0], tmp1[2]), float(tmp[3]), float(tmp[4]))

    def store_id_counter_dict(self):
        """speichert id_counter_dict in eine Txt-Datei"""
        # create_time = datetime.datetime.now().strftime("%Y_%m_%d__%H_%M_%S")
        while True:
            try:
                with open('id_counter_dict__' + self.start_time + '.txt',
                          'a') as counter_file:
                    print(datetime.datetime.now().strftime("%H_%M_%S"), '\t', self.id_counter_dict, file=counter_file)
                    time.sleep(5)

            except FileNotFoundError:
                with open('id_counter_dict__' + self.start_time + '.txt',
                          'w') as o:
                    print("Auftritte der einzelnen ID's:", file=o)

    def start_id_counter_thread(self):
        """startet Thread, welcher das id_counter_dict alle fuenf Sekunden in eine Datei schreibt"""
        store_counter_thread = threading.Thread(target=self.store_id_counter_dict, )
        store_counter_thread.start()

    def convert_unsigned_to_signed(self, number):
        """konvertiert, falls noetig, die Werte von unsigned to signed"""
        if self.conf_dict[number][0][0] == '8':
            number = numpy.int8(number)
        elif self.conf_dict[number][0][0] == '16':
            number = numpy.int16(number)
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
        """konvertiert integer Werte in Hex-Werte, setzt sie zusammen und gibt diese dezimal als integer zurueck"""
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
        """schneidet die ueberschuessigen Bytes ab und gibt diese Liste zurueck"""
        signal_strength = received_data[-2]
        new_list = received_data[4:-2]
        return new_list, signal_strength

    def lookup_position_and_ids_of_bytes_decimal_server(self, data):
        """iteriert durch empfangenes Daten-Paket und separiert IDs und Nutzdaten
         -> schickt jede id mit Wert direkt an den Webserver"""
        n_data, strength = self.discard_non_payload_bytes_return_signal_strength(data)
        # print('strength: ', strength)
        counter = 0
        temp = {}
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

                self.que.put({0: int(var[1]), 1: self.convert_bytes_to_value_decimal(var[1], *tmp)})

                # temp[var[1]] = self.convert_bytes_to_value_decimal(var[1], *tmp)
                counter += int(int(var[0]) / 8)


class SendingClass():
    """Klasse um die Konfigurationsdatei an das Funkmodul zu schicken"""

    def __init__(self, sender):
        self.__configuration = [[False, False, False, False, False, False, False, False],
                                [False, False, False, False, False, False, False, False],
                                [False, False, False, False, False, False, False, False],
                                [False, False, False, False, False, False, False, False]]

        self.sender = sender

    def set_configuration(self, data):
        """Funktion um die Konfiguration zu ueberpruefen und zu laden"""
        ok = True
        if len(data) != 4:
            ok = False
        else:
            for i in data:
                if len(i) != 8:
                    ok = False

        if ok:
            print('configuration ok')
            self.__configuration = data
            # self.send_message()
        else:
            sys.exit('wrong configuration')

    def _build_configuration_message(self):
        """Funktion um aus dem Konfigurationsarray die zu sendende Nachricht zu erstellen"""
        start_signal = '02'
        command = '00'
        length = '05'
        uart_signal = 'DD'
        message = ''
        payload = ['', '', '', '']
        for num, byte in enumerate(self.__configuration):
            for bit in byte:
                if bit:
                    payload[num] += '1'
                else:
                    payload[num] += '0'

        for i, j in enumerate(payload):
            b = str(hex(int(j[::-1], 2))).replace('0x', '')
            if len(b) % 2 != 0:  # Checks if the payload has an odd size and adds an leading zero
                b = '0' + b
            payload[i] = b

        message += start_signal
        message += command
        message += length
        message += uart_signal
        message += ''.join(payload)
        c = 0
        checksum = 0
        while c < len(message):  # going through the bytes of the string with a XOR
            checksum ^= int(message[c] + message[c + 1], 16)
            c += 2
        message += '{0:02X}'.format(checksum)
        print(message)
        return message

    def send_message(self):
        """Sendet die Konfigurationsnachricht"""
        data_to_send = self._build_configuration_message()
        AMB8826.send_data(self.sender, data_to_send)


def server(que):
    """startet den Webserver und schickt die Wertpaare, welche in der Queue ankommen an den Webserver"""
    # Config
    port = 7777  # Websocket Port

    # timeInterval = 10  # Milliseconds

    class WSHandler(tornado.websocket.WebSocketHandler):

        # check_origin fixes an error 403 with Tornado
        # http://stackoverflow.com/questions/24851207/tornado-403-get-warning-when-opening-websocket

        def check_origin(self, origin):
            return True

        def open(self):
            self.send_values()

        def send_values(self):
            while True:
                data = que.get()
                to_send_info = json.dumps(data)
                # print(to_send_info)
                self.write_message(to_send_info)

        def on_message(self, message):
            pass

        def on_close(self):
            pass

        def InputData(self, InputListe):
            SinputList = []
            for line in InputListe:
                # he call .decode('ascii') converts the raw bytes to a string.
                # .split(',') splits the string on commas.
                s = line.decode("utf-8").split(',')
                SinputList.append(s)
            return SinputList

    print("Server wird gestartet")
    application = tornado.web.Application([(r'/service', WSHandler), ])

    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    RP = ReceiveProtocol()
