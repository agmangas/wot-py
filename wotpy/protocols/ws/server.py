#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tornado import web
from slugify import slugify

from wotpy.protocols.server import BaseProtocolServer
from wotpy.protocols.ws.handler import WebsocketHandler


class WebsocketServer(BaseProtocolServer):
    """Websockets binding server implementation."""

    PORT = 81
    SCHEME = "ws"

    @classmethod
    def path_for_exposed_thing(cls, exposed_thing):
        """"""

        return r"/{}".format(slugify(exposed_thing.thing.name))

    def __init__(self, port=PORT, scheme=SCHEME):
        super(WebsocketServer, self).__init__(port, scheme)
        self._server = None

    def _build_app_handlers(self):
        """Builds a list of handlers for a Tornado application."""

        def _build_url_spec(exp_thng):
            return (
                self.path_for_exposed_thing(exp_thng),
                WebsocketHandler,
                {"exposed_thing": exp_thng}
            )

        return [
            _build_url_spec(exposed_thing)
            for exposed_thing in self._exposed_things.values()
        ]

    def build_app(self):
        """Builds an instance of a Tornado application to handle the WoT interface requests."""

        return web.Application(self._build_app_handlers())

    def regenerate_links(self):
        """Regenerates all link sub-documents for each interaction
        in the exposed things contained in this server."""

        pass

    def start(self):
        """Starts the server."""

        application = self.build_app()
        self._server = application.listen(self.port)

    def stop(self):
        """Stops the server."""

        if not self._server:
            return

        self._server.stop()
        self._server = None
