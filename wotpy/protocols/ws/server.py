#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Class that implements the WebSockets server.
"""

from tornado import web

from wotpy.codecs.enums import MediaTypes
from wotpy.protocols.enums import Protocols
from wotpy.protocols.server import BaseProtocolServer
from wotpy.protocols.ws.handler import WebsocketHandler
from wotpy.td.form import Form


class WebsocketServer(BaseProtocolServer):
    """WebSockets binding server implementation.
    Builds a Tornado application that uses the
    :py:class:`wotpy.protocols.ws.handler.WebsocketHandler`
    handler to process WebSockets messages."""

    DEFAULT_PORT = 81
    DEFAULT_PROTO = Protocols.WEBSOCKETS

    def __init__(self, port=DEFAULT_PORT, protocol=DEFAULT_PROTO):
        assert protocol in [Protocols.WEBSOCKETS]
        super(WebsocketServer, self).__init__(port=port, protocol=protocol)
        self._server = None
        self._app = self._build_app()

    @property
    def app(self):
        """Tornado application property."""

        return self._app

    def _build_app(self):

        """Builds and returns the Tornado application for the WebSockets server."""

        return web.Application([(
            r"/(?P<name>[^\/]+)",
            WebsocketHandler,
            {"websocket_server": self}
        )])

    def links_for_interaction(self, hostname, exposed_thing, interaction):
        """Builds and returns a list with all Links that
        relate to this server for the given Interaction."""

        base_url = self.get_thing_base_url(hostname=hostname, exposed_thing=exposed_thing)
        media_type = MediaTypes.JSON

        return [Form(interaction=interaction, protocol=self.protocol, href=base_url, media_type=media_type)]

    def get_thing_base_url(self, hostname, exposed_thing):
        """Returns the base URL for the given ExposedThing in the context of this server."""

        hostname = hostname.rstrip("/")
        thing_path = "{}".format(exposed_thing.thing.name)

        return "ws://{}:{}/{}".format(hostname, self.port, thing_path)

    def start(self):
        """Starts the server."""

        self._server = self.app.listen(self.port)

    def stop(self):
        """Stops the server."""

        if not self._server:
            return

        self._server.stop()
        self._server = None
