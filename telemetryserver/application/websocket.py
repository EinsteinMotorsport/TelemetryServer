import asyncio
import json

import tornado
import tornado.websocket

open_connections = []


class WebsocketHandler(tornado.websocket.WebSocketHandler):
    """
    Handle communication to one TelemetryClient

    For every new connection from the TelemetryClient to the server via
    websocket a new instance of this class is created. By using an eventloop
    tornado is able to maintain multiple connections in one thread,
    asynchronously.
    """
    def check_origin(self, origin):
        """
        Check origin of websocket connection

        Gets automatically called at time of establishing a new connection.

        Usually this method restricts websocket connections across
        different sites for security reasons. If this method is overwritten
        to always return True, connections from different sources are possible.

        Return:
            Always True
        """

        return True

    def open(self):
        """
        Handle new connection to TelemetryClient

        Event handler that is called for every new connection.

        Add every new websocket connection to a list as otherwise it wouldn't
        be possible to access any of the connections.
        """

        if self not in open_connections:
            open_connections.append(self)

    def on_message(self, message):
        """
        Handle incoming messages

        Event handler that is called for every incoming message.

        Empty, but needs to be implemented as it would otherwise raise a
        NotImplementedError.
        """
        pass

    def on_close(self):
        """
        Properly close connection to TelemetryClient

        Event handler that gets called when the connection is lost.

        Remove the websocket connection from the list as there is no need
        to access it anymore.
        """

        open_connections.remove(self)


async def consume(data_source):
    """
    Continuously receive telemetry and send it to all connected clients

    Asynchronously wait for telemetry data sent through a pipe and as soon
    as data is received, transform it into json format and send it
    asynchronously to all clients.

    Args:
        data_source (aioprocessing.Connection): One end of an asynchronously
        usable pipe through which telemetry data is provided for the server.
    """

    while True:
        telemetry_data = await data_source.coro_recv()

        # TODO: should the data be transformed to json here or should it
        #   already be a json string?
        telemetry_message = json.dumps(telemetry_data)

        # asynchronously send the message to all clients via websocket
        asyncio.gather(*[
            client.write_message(telemetry_message)
            for client in open_connections
        ])


def start_server(data_source, server_port=7777):
    """
    Start webserver for websocket connections to client

    Start asynchronous eventloop for tornado webserver and receiving data
    through a Pipe.

    Args:
        connection: One side of a pipe, should be a pipe that can be accessed
            asynchronously.

        server_port (int): TCP port on which the server will run.
            Defaults to 7777.
    """

    print("Starting server...")

    # New web application that provides Websocket connections via
    # WebsocketHandler class, that is available at the '/service' path
    # of the server
    application = tornado.web.Application([
        (r'/service', WebsocketHandler),
    ])

    # start server that listens to websocket connections
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(server_port)

    # start asyncio eventloop which is requried for tornado and for running
    # the async consum function
    # one could also use the tornado IOLoop, which is esentially the same as
    # the asyncio eventloop, but for running other async functions as well,
    # the tornado ioloop is not as suited.
    loop = asyncio.get_event_loop()

    # run the eventloop until consume stops, which does not happen
    loop.run_until_complete(consume(data_source))
