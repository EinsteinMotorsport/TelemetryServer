import serial

from telemetryserver.data import data_protocol_class_webserver

sender = serial.Serial(  # initialisiert den Empfaender am COM-Port
    port='COM5',
    baudrate=115200,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS)

Sender_Protocol = data_protocol_class_webserver.SendingClass(sender)  # Erstellt Instanz der Sender Klasse

#  Konfiguration der 8 Bytes fuer die Konfigurationsnachricht
config = [[True, False, False, False, False, False, False, False],
          [False, False, False, False, False, False, False, False],
          [False, False, False, False, False, False, False, False],
          [False, False, False, False, False, False, False, False]]

if __name__ == '__main__':
    Sender_Protocol.set_configuration(config)  # Konfiguration wird gesetzt
    Sender_Protocol.send_message()  # Konfiguration wird gesendet
