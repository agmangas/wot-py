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
    """WebSockets binding server implementation. Builds a Tornado application
    that uses the WebsocketHandler handler to process WebSockets messages."""

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

    def build_forms(self, hostname, interaction):
        """Builds and returns a list with all Form that are
        linked to this server for the given Interaction."""

        exposed_thing = self.exposed_thing_group.find_by_interaction(interaction)

        assert exposed_thing

        base_url = self.build_base_url(hostname=hostname, thing=exposed_thing.thing)
        media_type = MediaTypes.JSON

        return [Form(interaction=interaction, protocol=self.protocol, href=base_url, media_type=media_type)]

    def build_base_url(self, hostname, thing):
        """Returns the base URL for the given Thing in the context of this server."""

        assert self.exposed_thing_group.find_by_thing(thing)

        hostname = hostname.rstrip("/")
        thing_path = "{}".format(thing.url_name)

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
