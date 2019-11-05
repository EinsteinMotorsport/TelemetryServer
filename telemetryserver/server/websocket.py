import json

import tornado


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
    application = tornado.web.Application([
        (r'/service', WSHandler),
    ])

    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(port)
    tornado.ioloop.IOLoop.instance().start()
