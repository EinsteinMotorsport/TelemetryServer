import serial
from telemetryserver.data import data_protocol_class_webserver

if __name__ == '__main__':
    # initialisiert den Empfaenger am COM-Port
    sender = serial.Serial(port='COM5',
                           baudrate=115200,
                           parity=serial.PARITY_NONE,
                           stopbits=serial.STOPBITS_ONE,
                           bytesize=serial.EIGHTBITS)

    # Erstellt Instanz der Sender Klasse
    Sender_Protocol = data_protocol_class_webserver.SendingClass(sender)

    #  Konfiguration der 8 Bytes fuer die Konfigurationsnachricht
    config = [[True, False, False, False, False, False, False, False],
              [False, False, False, False, False, False, False, False],
              [False, False, False, False, False, False, False, False],
              [False, False, False, False, False, False, False, False]]

    # Konfiguration wird gesetzt
    Sender_Protocol.set_configuration(config)
    # Konfiguration wird gesendet
    Sender_Protocol.send_message()
