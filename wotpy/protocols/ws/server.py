#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Class that implements the WebSockets server.
"""

import tornado.gen
from tornado import web
from tornado.httpserver import HTTPServer

from wotpy.codecs.enums import MediaTypes
from wotpy.protocols.enums import Protocols
from wotpy.protocols.server import BaseProtocolServer
from wotpy.protocols.ws.enums import WebsocketSchemes
from wotpy.protocols.ws.handler import WebsocketHandler
from wotpy.wot.form import Form


class WebsocketServer(BaseProtocolServer):
    """WebSockets binding server implementation. Builds a Tornado application
    that uses the WebsocketHandler handler to process WebSockets messages."""

    DEFAULT_PORT = 81

    def __init__(self, port=DEFAULT_PORT, ssl_context=None):
        super(WebsocketServer, self).__init__(port=port)
        self._server = None
        self._app = self._build_app()
        self._ssl_context = ssl_context

    @property
    def protocol(self):
        """Protocol of this server instance.
        A member of the Protocols enum."""

        return Protocols.WEBSOCKETS

    @property
    def scheme(self):
        """Returns the URL scheme for this server."""

        return WebsocketSchemes.WSS if self.is_secure else WebsocketSchemes.WS

    @property
    def is_secure(self):
        """Returns True if this server is configured to use SSL encryption."""

        return self._ssl_context is not None

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

        exposed_thing = self.exposed_thing_set.find_by_interaction(interaction)

        if not exposed_thing:
            raise ValueError("Unknown Interaction")

        base_url = self.build_base_url(hostname=hostname, thing=exposed_thing.thing)

        return [
            Form(
                interaction=interaction,
                protocol=self.protocol,
                href=base_url,
                content_type=MediaTypes.JSON)
        ]

    def build_base_url(self, hostname, thing):
        """Returns the base URL for the given Thing in the context of this server."""

        if not self.exposed_thing_set.find_by_thing_id(thing.id):
            raise ValueError("Unknown Thing")

        hostname = hostname.rstrip("/")

        return "{}://{}:{}/{}".format(self.scheme, hostname, self.port, thing.url_name)

    @tornado.gen.coroutine
    def start(self):
        """Starts the WebSockets server."""

        self._server = HTTPServer(self.app, ssl_options=self._ssl_context)
        self._server.listen(self.port)

    @tornado.gen.coroutine
    def stop(self):
        """Stops the WebSockets server."""

        if not self._server:
            return

        self._server.stop()
        self._server = None
