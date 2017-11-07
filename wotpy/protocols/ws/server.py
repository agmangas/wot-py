#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tornado import web
from slugify import slugify

from wotpy.td.link import Link
from wotpy.protocols.enums import Protocols
from wotpy.protocols.server import BaseProtocolServer
from wotpy.protocols.ws.handler import WebsocketHandler


class WebsocketServer(BaseProtocolServer):
    """Websockets binding server implementation."""

    DEFAULT_PORT = 81
    DEFAULT_PROTO = Protocols.WEBSOCKETS

    @classmethod
    def path_for_exposed_thing(cls, exposed_thing):
        """Builds and returns the WebSockets endpoint path for the given ExposedThing.
        This method is deterministic and the same thing will always produce the same path."""

        return r"/{}".format(slugify(exposed_thing.thing.name))

    def __init__(self, port=DEFAULT_PORT, protocol=DEFAULT_PROTO):
        assert protocol in [Protocols.WEBSOCKETS]
        super(WebsocketServer, self).__init__(port=port, protocol=protocol)
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

    def _link_for_exposed_thing(self, interaction, exposed_thing):
        """Builds the Link instance that relates to this server for the given interaction."""

        return Link(
            interaction=interaction,
            protocol=self.protocol,
            href=self.path_for_exposed_thing(exposed_thing=exposed_thing))

    def build_app(self):
        """Builds an instance of a Tornado application to handle the WoT interface requests."""

        return web.Application(self._build_app_handlers())

    def regenerate_links(self):
        """Regenerates all link sub-documents for each interaction
        in the exposed things contained in this server."""

        self._clean_protocol_links()

        for exp_thing in self._exposed_things.values():
            for interaction in exp_thing.thing.interaction:
                link = self._link_for_exposed_thing(interaction, exp_thing)
                interaction.add_link(link)

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
