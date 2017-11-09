#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tornado import web

from wotpy.protocols.enums import Protocols
from wotpy.protocols.server import BaseProtocolServer
from wotpy.protocols.ws.handler import WebsocketHandler
from wotpy.td.link import Link


class WebsocketServer(BaseProtocolServer):
    """Websockets binding server implementation."""

    DEFAULT_PORT = 81
    DEFAULT_PROTO = Protocols.WEBSOCKETS

    @classmethod
    def path_for_exposed_thing(cls, exposed_thing):
        """Builds and returns the WebSockets endpoint path for the given ExposedThing.
        This method is deterministic and the same thing will always produce the same path."""

        return r"/{}".format(exposed_thing.thing.name)

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

        hostname = hostname.rstrip("/")
        base_url = "ws://{}:{}".format(hostname, self.port)
        path_url = self.path_for_exposed_thing(exposed_thing=exposed_thing)
        path_url = path_url.lstrip("/")
        href = "{}/{}".format(base_url, path_url)

        return [Link(interaction=interaction, protocol=self.protocol, href=href)]

    def start(self):
        """Starts the server."""

        self._server = self.app.listen(self.port)

    def stop(self):
        """Stops the server."""

        if not self._server:
            return

        self._server.stop()
        self._server = None
