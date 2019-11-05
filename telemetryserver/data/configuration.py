import sys

from telemetryserver.transmission import AMB8826


class SendingClass():
    """Klasse um die Konfigurationsdatei an das Funkmodul zu schicken"""
    def __init__(self, sender):
        self.__configuration = [
            [False, False, False, False, False, False, False, False],
            [False, False, False, False, False, False, False, False],
            [False, False, False, False, False, False, False, False],
            [False, False, False, False, False, False, False, False]
        ]

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
        """
        Funktion um aus dem Konfigurationsarray die zu sendende
        Nachricht zu erstellen
        """

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
        """Sendet die Konfigurationsnachricht"""

        data_to_send = self._build_configuration_message()
        AMB8826.send_data(self.sender, data_to_send)
