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
        self._app = self._build_app()

    @property
    def app(self):
        """Tornado application property."""

        return self._app

    def _build_app(self):
        """"""

        return web.Application([(
            r"/(?P<name>[^\/]+)",
            WebsocketHandler,
            {"websocket_server": self}
        )])

    def _link_for_interaction(self, interaction, exposed_thing):
        """Builds the Link instance that relates to this server for the given interaction."""

        return Link(
            interaction=interaction,
            protocol=self.protocol,
            href=self.path_for_exposed_thing(exposed_thing=exposed_thing))

    def regenerate_links(self):
        """Regenerates all link sub-documents for each interaction
        in the exposed things contained in this server."""

        def _clean_protocol_links(the_exposed_thing):
            """Removes all interaction links related to this
            server protocol for the given ExposedThing."""

            for the_interaction in the_exposed_thing.thing.interaction:
                links_to_remove = [
                    the_link for the_link in the_interaction.link
                    if the_link.protocol == self.protocol
                ]

                for the_link in links_to_remove:
                    the_interaction.remove_link(the_link)

        for exposed_thing in self._exposed_things.values():
            _clean_protocol_links(exposed_thing)

            for interaction in exposed_thing.thing.interaction:
                link = self._link_for_interaction(interaction, exposed_thing)
                interaction.add_link(link)

    def start(self):
        """Starts the server."""

        self._server = self.app.listen(self.port)

    def stop(self):
        """Stops the server."""

        if not self._server:
            return

        self._server.stop()
        self._server = None
