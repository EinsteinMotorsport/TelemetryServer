from multiprocessing import Process, SimpleQueue

import serial
import serial.tools.list_ports
from telemetryserver.data import data_protocol_class_webserver
from telemetryserver.transmission import AMB8826

if __name__ == '__main__':

    ports = list(serial.tools.list_ports.comports())

    for port in ports:
        if "" in port.hwid:
            portinfo = str(port).split()
            portnumber = portinfo[0]
            print(portnumber)

    # initialisiert den Empfaenger am COM-Port
    receiver = serial.Serial(port=portnumber,
                             baudrate=115200,
                             parity=serial.PARITY_NONE,
                             stopbits=serial.STOPBITS_ONE,
                             bytesize=serial.EIGHTBITS)

    # Erstellt Instanz von SimpleQueue
    # ueber diese laeuft die interne Kommunikation zwischen Empfaenger
    # und Webserver-Process
    q = SimpleQueue()

    # Erstellt Instanz der Empfaenger Klasse
    Protocol = data_protocol_class_webserver.ReceiveProtocol(queue=q)

    # Instanz von parallelen Prozess mit Webserver wird erstellt
    p = Process(target=data_protocol_class_webserver.server, args=(q, ))

    # Prozess wird gestartet
    p.start()

    while True:
        # Daten werden empfangen
        received_data = AMB8826.get_answer_address_mode_1(receiver)

        # print(len(received_data))

        # Daten werden zur Verarbeitung an die Klasse uebergeben
        # in der Klasse wird auch upload geregelt
        Protocol.setincoming_data(received_data)
