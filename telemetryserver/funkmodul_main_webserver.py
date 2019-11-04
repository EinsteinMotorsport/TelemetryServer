import serial

import AMB8826
import data_protocol_class_webserver
from multiprocessing import Process, SimpleQueue

if __name__ == '__main__':
    receiver = serial.Serial(  # initialisiert den Empfaender am COM-Port
        port='COM8',
        baudrate=115200,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS)

    q = SimpleQueue()
    # Erstellt Instanz von SimpleQueue; ueber diese laeuft die interne Kommunikation zwischen Empfaenger und Webserver-Process

    Protocol = data_protocol_class_webserver.ReceiveProtocol(queue=q)  # Erstellt Instanz der Empfaenger Klasse
    p = Process(target=data_protocol_class_webserver.server, args=(q,))
    # Instanz von parallelen Prozess mit Webserver wird erstellt

    p.start()  # Prozess wird gestartet

    while True:
        received_data = AMB8826.get_answer_address_mode_1(receiver)  # Daten werden empfangen
        # print(len(received_data))
        Protocol.setincoming_data(received_data)
        # Daten werden zur Verarbeitung an die Klasse uebergeben; in der Klasse wird auch upload geregelt
